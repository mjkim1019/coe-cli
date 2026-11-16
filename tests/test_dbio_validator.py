import tempfile
import unittest
from pathlib import Path

from actions.dbio_validator import is_dbio_file, validate_dbio
from actions.file_manager import FileManager

PROD = 'ZORD_PROD_GRP_DTL'
DC = 'ZORD_DC_GRP_DTL'


class DbioValidatorTests(unittest.TestCase):
    def check(self, sql, expected, path='query.sql'):
        result = validate_dbio(path, sql)
        self.assertEqual(result['status'], 'COMPLETE', result)
        issues = [d for d in result['diagnostics'] if d['severity'] == 'CRITICAL']
        self.assertEqual(len(issues), expected, result)
        return issues

    def test_product_truth_table(self):
        for eff in (False, True):
            for supl in (False, True):
                with self.subTest(eff=eff, supl=supl):
                    conditions = ['1=1']
                    if eff:
                        conditions.append('EFF_END_DTM=:dt')
                    if supl:
                        conditions.append('SUPL_FUNC_PSBL_END_DT>=:dt')
                    self.check(f"select * from {PROD} where {' and '.join(conditions)}", int(not (eff and supl)))

    def test_discount_truth_table(self):
        for eff in (False, True):
            for op in (False, True):
                with self.subTest(eff=eff, op=op):
                    conditions = ['1=1']
                    if eff:
                        conditions.append('EFF_END_DTM=:dt')
                    if op:
                        conditions.append('OP_PSBL_END_DT>=:dt')
                    self.check(f"select * from {DC} where {' and '.join(conditions)}", int(not (eff or op)))

    def test_non_predicate_mentions(self):
        self.check(f"select EFF_END_DTM, SUPL_FUNC_PSBL_END_DT from {PROD} where id=1 /* EFF_END_DTM=1 and SUPL_FUNC_PSBL_END_DT=1 */", 1)
        self.check(f"select * from {PROD} where x='EFF_END_DTM SUPL_FUNC_PSBL_END_DT'", 1)
        self.check(f"update {PROD} set EFF_END_DTM=:dt, SUPL_FUNC_PSBL_END_DT=:dt where id=1", 1)

    def test_alias_isolation(self):
        self.check(f'select * from {PROD} a join other b on a.id=b.id where b.EFF_END_DTM=1 and b.SUPL_FUNC_PSBL_END_DT=1', 1)
        issues = self.check(f'select * from {DC} a join {DC} b on a.id=b.id where a.EFF_END_DTM=1', 1)
        self.assertEqual(issues[0]['alias'], 'b')
        self.check(f'select * from {DC} a join other b on a.id=b.id where EFF_END_DTM=1', 1)

    def test_query_isolation(self):
        self.check(f'select * from {DC} where EFF_END_DTM=1; select * from {DC}', 1)
        self.check(f'select * from {DC} where EFF_END_DTM=1 union all select * from {DC}', 1)
        self.check(f'select * from {DC} a where exists (select 1 from other a where a.EFF_END_DTM=1)', 1)
        self.check(f'select * from {DC} a where exists (select 1 from {DC} b where b.EFF_END_DTM=1)', 1)

    def test_join_and_cte(self):
        self.check(f'select * from other a join {PROD} b on a.id=b.id and b.EFF_END_DTM=1 and b.SUPL_FUNC_PSBL_END_DT=1', 0)
        self.check(f'select * from {DC} a left join other b on a.EFF_END_DTM=1', 1)
        self.check(f'select * from other a left join {DC} b on b.EFF_END_DTM=1', 0)
        self.check(f'with x as (select * from {DC} where EFF_END_DTM=1) select * from x', 0)
        self.check(f'with {DC} as (select * from other) select * from {DC}', 0)

    def test_or_branches(self):
        self.check(f'select * from {DC} where EFF_END_DTM=1 or OP_PSBL_END_DT=1', 0)
        self.check(f'select * from {DC} where EFF_END_DTM=1 or id=1', 1)
        self.check(f'select * from {PROD} where EFF_END_DTM=1 or SUPL_FUNC_PSBL_END_DT=1', 1)

    def test_case_schema_and_predicates(self):
        self.check(f'select * from owner.{DC.lower()} a where :dt between a.eff_end_dtm and :end', 0)
        self.check(f'select * from "{DC}" "A" where "A"."OP_PSBL_END_DT" in (:dt, :end)', 0)
        self.check(f'select * from {DC} where EFF_END_DTM is null', 0)
        self.check(f'select * from {DC} a, other b where a.id=b.id(+) and a.EFF_END_DTM=:dt', 0)

    def test_scope_and_file_filter(self):
        for path in ['pdb_test', 'PDB_TEST.h', 'test.SQL', r'C:\work\pdb_test.pc']:
            self.assertTrue(is_dbio_file(path))
            self.check(f'select * from {DC}', 1, path)
        for path in ['test.c', 'not_pdb_test.h', '/pdb_dir/test.h']:
            self.assertFalse(is_dbio_file(path))
            self.assertEqual(validate_dbio(path, f'select * from {DC}')['status'], 'NOT_APPLICABLE')
        self.check(f'/* select * from {DC} */\nint some_variable;', 0, 'pdb_header.h')
        self.check(f'select \'{DC}\' from unrelated', 0)
        self.check(f'insert into {DC} (id) values (1)', 0)
        self.check(f'insert into other select * from {DC}', 1)

    def test_embedded_and_lines(self):
        issues = self.check(f'void f() {{\n EXEC SQL SELECT * FROM {DC};\n}}', 1, 'pdb_test.pc')
        self.assertEqual(issues[0]['line'], 2)
        self.check(f'EXEC SQL INCLUDE sqlca;\nEXEC SQL SELECT * FROM {DC} WHERE EFF_END_DTM=:dt;', 0, 'pdb_test.pc')

    def test_cursor_and_not_null(self):
        self.check(f'EXEC SQL DECLARE c CURSOR FOR SELECT * FROM {DC};', 1, 'pdb_cursor.pc')
        self.check(f'select * from {DC} where EFF_END_DTM is not null', 0)
        self.check(f"/* EXEC SQL SELECT * FROM other; */ select * from {DC}", 1)

    def test_parse_failure(self):
        result = validate_dbio('bad.sql', f'select * from {PROD} where (')
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertEqual(result['diagnostics'][0]['code'], 'DBIO_PARSE_ERROR')

    def test_file_manager_add_and_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'pdb_sample'
            path.write_text(f'select * from {DC}', encoding='utf-8')
            manager = FileManager()
            result = manager.add([str(path)])
            self.assertIn('CRITICAL DBIO002', '\n'.join(result['messages']))
            self.assertEqual(result['analyses'][0]['analysis']['dbio_validation']['diagnostics'][0]['code'], 'DBIO002')
            path.write_text(f'select * from {DC} where EFF_END_DTM=:dt', encoding='utf-8')
            self.assertNotIn('CRITICAL', manager.add_single_file(str(path))['message'])
            path.write_text(f'select * from {DC}', encoding='utf-8')
            self.assertIn('CRITICAL', '\n'.join(manager.add_directory(directory)))


if __name__ == '__main__':
    unittest.main()
