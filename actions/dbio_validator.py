"""Deterministic Oracle DBIO predicate checks, independent of LLM output."""
import re
from pathlib import PureWindowsPath

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer.scope import traverse_scope

RULES = {
    'ZORD_PROD_GRP_DTL': (
        'DBIO001', ({'EFF_END_DTM'}, {'SUPL_FUNC_PSBL_END_DT'})),
    'ZORD_DC_GRP_DTL': (
        'DBIO002', ({'EFF_END_DTM', 'OP_PSBL_END_DT'},)),
}
QUERY_TYPES = (exp.Select, exp.Update, exp.Delete, exp.Merge)


def is_dbio_file(path):
    name = PureWindowsPath(str(path)).name.lower()
    return name.startswith('pdb_') or name.endswith('.sql')


def _owner(node):
    return node.find_ancestor(*QUERY_TYPES)


def _coverage(node, table, query, single_source, groups):
    """Require coverage on every OR branch; combine predicates across AND."""
    if node is None:
        return set()
    if isinstance(node, (exp.Paren, exp.Where)):
        return _coverage(node.this, table, query, single_source, groups)
    if isinstance(node, (exp.And, exp.Or)):
        left = _coverage(node.this, table, query, single_source, groups)
        right = _coverage(node.expression, table, query, single_source, groups)
        return left | right if isinstance(node, exp.And) else left & right
    if isinstance(node, exp.Not) and isinstance(node.this, exp.Predicate):
        return _coverage(node.this, table, query, single_source, groups)
    # Only actual comparison predicates count, never SELECT/SET expressions,
    # literals, subquery predicates or CASE conditions buried in an expression.
    if not isinstance(node, exp.Predicate):
        return set()
    columns = set()
    for column in node.find_all(exp.Column):
        if _owner(column) is not query:
            continue
        if column.find_ancestor(exp.Case) is not None:
            continue
        qualifier = column.table.upper()
        if qualifier == table.alias_or_name.upper() or (not qualifier and single_source):
            columns.add(column.name.upper())
    return {i for i, alternatives in enumerate(groups) if columns & alternatives}


def validate_dbio(path, content):
    """Return status and diagnostics. Unparseable SQL is never a clean pass.

    Supports plain Oracle SQL and EXEC SQL blocks in pdb_* sources. Dynamic SQL
    inside C strings is not evaluated. Header-only files have no queries.
    """
    result = {'status': 'NOT_APPLICABLE', 'diagnostics': []}
    if not is_dbio_file(path):
        return result
    result['status'] = 'COMPLETE'
    # Tokenize first so SQL keywords in comments/strings do not trigger checks.
    try:
        tokens = sqlglot.Dialect.get_or_raise('oracle').tokenize(content)
    except SqlglotError:
        tokens = []
    sql_words = {'SELECT', 'UPDATE', 'DELETE', 'MERGE', 'INSERT', 'WITH'}
    starts = [t for t in tokens if t.text.upper() in sql_words
              and t.token_type.name not in {'STRING', 'IDENTIFIER'}]
    if not starts:
        if re.search(r'\b(?:SELECT|UPDATE|DELETE|MERGE)\b', content, re.I) and not tokens:
            result['status'] = 'INCOMPLETE'
            result['diagnostics'].append(_parse_error(path, 1))
        return result
    # Embedded Pro*C statements are independent SQL units. Offset line numbers
    # to the original source; non-query EXEC SQL declarations are ignored.
    units = []
    for i, token in enumerate(tokens[:-1]):
        if token.text.upper() != 'EXEC' or tokens[i + 1].text.upper() != 'SQL':
            continue
        end = next((t.start for t in tokens[i + 2:] if t.token_type.name == 'SEMICOLON'), len(content))
        start = tokens[i + 1].end + 1
        sql = content[start:end]
        cursor = re.match(r'\s*DECLARE\s+\w+\s+CURSOR\s+FOR\s+', sql, re.I)
        if cursor:
            start += cursor.end()
            sql = content[start:end]
        if re.match(r'\s*(?:SELECT|UPDATE|DELETE|MERGE|INSERT|WITH)\b', sql, re.I):
            units.append((sql, content[:start].count('\n')))
    if not units:
        units = [(content, 0)]
    for sql, offset in units:
        try:
            trees = sqlglot.parse(sql, read='oracle')
        except SqlglotError:
            result['status'] = 'INCOMPLETE'
            result['diagnostics'].append(_parse_error(path, offset + 1))
            continue
        for tree in trees:
            if tree is None:
                continue
            if isinstance(tree, exp.Command):
                result['status'] = 'INCOMPLETE'
                result['diagnostics'].append(_parse_error(path, offset + 1))
                continue
            # Resolve SELECT sources so CTE names are not mistaken for tables.
            scopes = {id(s.expression): s for s in traverse_scope(tree)}
            for query in tree.walk():
                if not isinstance(query, QUERY_TYPES):
                    continue
                scope = scopes.get(id(query))
                if scope is not None:
                    sources = list(scope.selected_sources.values())
                    tables = [source for _, source in sources if isinstance(source, exp.Table)]
                    single_source = len(sources) == 1
                else:
                    tables = [t for t in query.find_all(exp.Table) if _owner(t) is query]
                    single_source = len(tables) == 1
                for table in tables:
                    rule = RULES.get(table.name.upper())
                    if rule is None:
                        continue
                    code, groups = rule
                    coverage = _coverage(query.args.get('where'), table, query, single_source, groups)
                    for join in query.args.get('joins') or []:
                        # Outer JOIN ON does not filter its preserved side.
                        side = (join.side or '').upper()
                        if side == 'FULL' or (side == 'LEFT' and join.this is not table) or (side == 'RIGHT' and join.this is table):
                            continue
                        coverage |= _coverage(join.args.get('on'), table, query, single_source, groups)
                    if isinstance(query, exp.Merge):
                        coverage |= _coverage(query.args.get('on'), table, query, single_source, groups)
                    missing = [' 또는 '.join(sorted(g)) for i, g in enumerate(groups) if i not in coverage]
                    if missing:
                        identifier = table.this
                        line = identifier.meta.get('line', 1) + offset
                        result['diagnostics'].append({
                            'severity': 'CRITICAL', 'code': code, 'file': str(path),
                            'line': line, 'table': table.name.upper(),
                            'alias': table.alias_or_name, 'missing': missing,
                            'message': f"{table.name.upper()} ({table.alias_or_name}): 필수 조건 누락 — {' / '.join(missing)}",
                        })
    return result


def _parse_error(path, line):
    return {'severity': 'WARNING', 'code': 'DBIO_PARSE_ERROR', 'file': str(path),
            'line': line, 'message': 'SQL을 해석할 수 없어 필수 조건 검사를 완료하지 못했습니다. 수동 확인이 필요합니다.'}
