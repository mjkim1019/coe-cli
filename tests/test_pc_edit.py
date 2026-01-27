#!/usr/bin/env python3
"""
Pro*C (.pc) 파일 edit 기능 테스트

bf(before) → af(after) 변경이 실제 LLM 호출 → EditBlockCoder 파싱을 통해
올바르게 적용되는지 End-to-End로 검증한다.

변경사항:
  1. 헤더 주석에 변경이력 4줄 추가
  2. INIT2VCHAR(gst_sec_06) 1줄 추가
"""
import os
import sys
import shutil
import tempfile
import difflib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# 가상환경 경로 추가
venv_path = PROJECT_ROOT / '.venv' / 'lib' / 'python3.13' / 'site-packages'
if venv_path.exists():
    sys.path.insert(0, str(venv_path))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

sys.path.insert(0, str(PROJECT_ROOT))

from actions.file_manager import FileManager
from actions.file_editor import FileEditor
from llm.service import LLMService
from cli.coders.editblock_coder import EditBlockCoder
from cli.core.context_manager import PromptBuilder

FIXTURES_DIR = PROJECT_ROOT / 'tests' / 'fixtures'
BF_FILE = FIXTURES_DIR / 'zinvbreps8030_bf.pc'
AF_FILE = FIXTURES_DIR / 'zinvbreps8030_af.pc'


def load_fixture(path: Path) -> str:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def diff_summary(content_a: str, content_b: str, label_a='result', label_b='expected', max_show=10) -> str:
    """두 내용의 차이를 요약 문자열로 반환"""
    lines_a = content_a.splitlines()
    lines_b = content_b.splitlines()
    diffs = list(difflib.unified_diff(lines_a, lines_b, lineterm='', fromfile=label_a, tofile=label_b, n=1))
    if not diffs:
        return "  (동일)"
    added = sum(1 for d in diffs if d.startswith('+') and not d.startswith('+++'))
    removed = sum(1 for d in diffs if d.startswith('-') and not d.startswith('---'))
    lines_summary = f"  +{added} -{removed} lines"
    detail = '\n'.join(diffs[:max_show * 2])
    return f"{lines_summary}\n{detail}"


# ---------------------------------------------------------------------------
# Test 1: FileManager가 .pc 파일을 pc_file 타입으로 인식하고 분석하는지
# ---------------------------------------------------------------------------
def test_pc_file_add():
    """FileManager가 .pc 파일을 올바르게 추가하고 분석하는지 검증"""
    fm = FileManager()
    result = fm.add_single_file(str(BF_FILE))

    assert result['file_type'] == 'pc_file', f"Expected pc_file, got {result['file_type']}"
    assert result['analysis'] is not None, "Analysis should not be None"
    assert str(BF_FILE) in fm.files, "File should be in files dict"
    assert str(BF_FILE) in fm.pc_file_info, "File should be in pc_file_info cache"

    analysis = result['analysis']
    assert len(analysis['exec_sql_includes']) > 0, "Should find EXEC SQL INCLUDE statements"
    assert len(analysis['cursors']) > 0, "Should find cursor declarations"
    assert len(analysis['functions']) > 0, "Should find function declarations"

    print(f"  file_type: {result['file_type']}")
    print(f"  EXEC SQL INCLUDE: {len(analysis['exec_sql_includes'])}개")
    print(f"  host_variables: {len(analysis['host_variables'])}개")
    print(f"  cursors: {len(analysis['cursors'])}개")
    print(f"  functions: {len(analysis['functions'])}개")
    print(f"  file_io_structs: {len(analysis['file_io_structs'])}개")
    print(f"  program_header: {analysis['program_header']}")

    return fm


# ---------------------------------------------------------------------------
# Test 2: zngm.h 자동 로드 확인
# ---------------------------------------------------------------------------
def test_zngm_auto_load():
    """Pro*C 파일 add 시 zngm.h가 자동으로 로드되는지 검증"""
    fm = FileManager()

    # zngm.h가 fixtures에 있는지 확인
    zngm_path = FIXTURES_DIR / 'zngm.h'
    if not zngm_path.exists():
        print("  SKIP: zngm.h fixture 파일이 없음")
        return

    result = fm.add_single_file(str(BF_FILE))

    # zngm.h가 자동으로 로드되었는지 확인
    zngm_loaded = any('zngm.h' in path for path in fm.files.keys())
    assert zngm_loaded, "zngm.h should be auto-loaded when adding .pc file"
    assert 'Auto-loaded' in result['message'], f"Message should contain Auto-loaded: {result['message']}"

    print(f"  message: {result['message']}")
    print(f"  총 로드된 파일 수: {len(fm.files)}")


# ---------------------------------------------------------------------------
# Test 3: 실제 LLM 호출 → EditBlockCoder 파싱 → bf → af 변환 E2E 검증
# ---------------------------------------------------------------------------
def test_editblock_bf_to_af():
    """실제 LLM에게 수정 요청 → 응답을 EditBlockCoder로 파싱 → bf→af 결과 검증

    실제 CLI 흐름과 동일하게:
    1. FileManager.add_single_file() → .pc 파일 로드
    2. PromptBuilder('edit') + set_coder_prompts(EditBlockPrompts) → 메시지 구성
    3. LLMService.chat_completion() → LLM 호출
    4. EditBlockCoder.parse_response() → SEARCH/REPLACE 파싱
    5. af 파일과 비교
    """
    bf_content = load_fixture(BF_FILE)
    af_content = load_fixture(AF_FILE)

    # 1. FileManager로 .pc 파일 로드 (실제 /add 흐름)
    file_manager = FileManager()
    file_manager.add_single_file(str(BF_FILE))
    # .pc 파일만 컨텍스트에 포함 (zngm.h는 제외 — LLM 혼동 방지)
    context_files = {
        k: v for k, v in file_manager.files.items()
        if k.endswith('.pc')
    }
    print(f"  컨텍스트 파일 수: {len(context_files)} (zngm.h 제외)")

    # 2. PromptBuilder + EditBlockCoder 프롬프트로 메시지 구성 (실제 /edit block 흐름)
    file_editor = FileEditor(backup_dir=tempfile.mkdtemp())
    coder = EditBlockCoder(file_editor)

    prompt_builder = PromptBuilder('edit')
    prompt_builder.set_coder_prompts(coder.prompts)  # EditBlockPrompts 설정

    user_request = (
        "이 파일에 다음 두 가지를 수정해줘:\n"
        "1. 파일 상단 변경이력 주석에 아래 내용을 추가해줘 "
        "(기존 '미납금액    ==> 미납요금 : 상동' 줄 다음에):\n"
        "    20260108    이춘세      <요청자> 자체개선\n"
        "                          <수정자> 이춘세 (청구)\n"
        "                          <변경내용> 06 sect write 초기화 처리\n"
        "                                  미사용함수 코멘트 처리\n"
        "\n"
        "2. INIT2VCHAR(gst_reisu); 줄 다음에 아래 코드를 추가해줘:\n"
        "        INIT2VCHAR(gst_sec_06);    /* 20260108 */\n"
    )
    messages = prompt_builder.build(user_request, context_files, [], file_manager)
    print(f"  프롬프트 메시지 수: {len(messages)}")

    # 3. LLM 호출 (실제 llm_service.chat_completion)
    llm_service = LLMService()
    print("  LLM 호출 중...")
    llm_response = llm_service.chat_completion(messages)

    if not llm_response or "choices" not in llm_response:
        print("  SKIP: LLM 서버 연결 실패 (서버가 실행 중인지 확인)")
        return 'skip'

    response_content = llm_response["choices"][0]["message"]["content"]
    print(f"  LLM 응답 길이: {len(response_content)}")
    print(f"  응답 미리보기: {response_content[:200]}...")

    # 4. EditBlockCoder로 파싱 (실제 coder.parse_response 흐름)
    parsed = coder.parse_response(response_content, context_files)

    if not parsed:
        print("  ❌ FAIL: EditBlockCoder가 응답을 파싱하지 못함")
        print(f"  응답 전체:\n{response_content[:500]}...")
        assert False, "EditBlockCoder failed to parse LLM response"

    # 파싱된 파일 경로 확인 (절대경로/상대경로 둘 다 가능)
    target_path = None
    for key in parsed.keys():
        if 'zinvbreps8030_bf.pc' in key:
            target_path = key
            break

    assert target_path is not None, f"bf.pc not found in parsed keys: {list(parsed.keys())}"
    result_content = parsed[target_path]
    print(f"  파싱된 파일: {target_path}")
    print(f"  결과 라인 수: {len(result_content.splitlines())}")

    # 5. af 파일과 비교
    if result_content == af_content:
        print("  PASS: bf → af 변환 완벽 일치")
        return True

    # 완벽 일치가 아닌 경우 — 핵심 변경사항이 포함되었는지 검증
    has_history = '20260108' in result_content and '이춘세' in result_content
    has_init = 'INIT2VCHAR(gst_sec_06)' in result_content

    print(f"  변경이력 추가됨: {'✅' if has_history else '❌'}")
    print(f"  INIT2VCHAR 추가됨: {'✅' if has_init else '❌'}")

    if has_history and has_init:
        print("  PASS: 핵심 변경사항 모두 포함 (공백/포맷 차이 존재)")
        print(diff_summary(result_content, af_content))
        return True
    else:
        print("  FAIL: 핵심 변경사항 누락")
        print(diff_summary(result_content, af_content))
        assert False, f"Missing changes: history={has_history}, init={has_init}"


# ---------------------------------------------------------------------------
# Test 4: FileEditor로 실제 파일에 적용 + 롤백
# ---------------------------------------------------------------------------
def test_apply_and_rollback():
    """FileEditor로 실제 파일 적용 후 롤백이 되는지 검증"""
    bf_content = load_fixture(BF_FILE)
    af_content = load_fixture(AF_FILE)

    # 임시 디렉토리에서 작업
    with tempfile.TemporaryDirectory() as tmpdir:
        work_file = os.path.join(tmpdir, 'zinvbreps8030_bf.pc')
        shutil.copy2(str(BF_FILE), work_file)

        file_editor = FileEditor(backup_dir=os.path.join(tmpdir, 'backups'))

        # 변경 적용
        operation = file_editor.apply_changes_from_dict(
            {work_file: af_content},
            "bf → af 변환 테스트"
        )

        assert len(operation.changes) == 1
        print(f"  operation_id: {operation.operation_id}")
        print(f"  변경된 파일 수: {len(operation.changes)}")

        # 적용 결과 확인
        with open(work_file, 'r', encoding='utf-8', errors='replace') as f:
            applied_content = f.read()
        assert applied_content == af_content, "Applied content should match af"
        print("  PASS: 파일 적용 확인")

        # 롤백
        rollback_ok = file_editor.rollback_operation(operation.operation_id)
        assert rollback_ok, "Rollback should succeed"

        with open(work_file, 'r', encoding='utf-8', errors='replace') as f:
            rolled_back = f.read()
        assert rolled_back == bf_content, "Rolled back content should match bf"
        print("  PASS: 롤백 확인")


# ---------------------------------------------------------------------------
# Test 5: 대용량 파일에서 SEARCH 블록 매칭 정확도
# ---------------------------------------------------------------------------
def test_search_block_precision():
    """6000줄 이상의 대용량 .pc 파일에서 SEARCH 블록이 정확히 매칭되는지 검증"""
    bf_content = load_fixture(BF_FILE)

    file_editor = FileEditor(backup_dir=tempfile.mkdtemp())
    coder = EditBlockCoder(file_editor)

    file_path = str(BF_FILE)

    # 존재하지 않는 블록으로 매칭 시도 → 원본 유지 확인
    bad_response = f"""{BF_FILE.name}
<<<<<<< SEARCH
        THIS_BLOCK_DOES_NOT_EXIST_IN_FILE();
        ANOTHER_FAKE_LINE();
=======
        REPLACED_LINE();
>>>>>>> REPLACE
"""

    context_files = {file_path: bf_content}
    parsed = coder.parse_response(bad_response, context_files)

    if file_path in parsed:
        # 매칭 실패 시 원본이 유지되어야 함
        assert parsed[file_path] == bf_content, "Unmatched SEARCH block should leave content unchanged"
        print("  PASS: 매칭 실패 시 원본 유지 확인")
    else:
        print("  PASS: 파싱 결과 없음 (정상)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    print("=" * 60)
    print("Pro*C (.pc) Edit 기능 테스트")
    print("=" * 60)

    # 사전 조건 확인
    assert BF_FILE.exists(), f"Missing fixture: {BF_FILE}"
    assert AF_FILE.exists(), f"Missing fixture: {AF_FILE}"

    tests = [
        ("1. .pc 파일 add 및 분석", test_pc_file_add),
        ("2. zngm.h 자동 로드", test_zngm_auto_load),
        ("3. LLM E2E: EditBlock bf→af 변환", test_editblock_bf_to_af),
        ("4. 파일 적용 및 롤백", test_apply_and_rollback),
        ("5. SEARCH 블록 매칭 정확도", test_search_block_precision),
    ]

    passed = 0
    failed = 0
    skipped = 0
    errors = []

    for name, func in tests:
        print(f"\n--- {name} ---")
        try:
            result = func()
            if result == 'skip':
                print(f"  ⏭️  SKIPPED")
                skipped += 1
            else:
                print(f"  ✅ PASSED")
                passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
            errors.append((name, str(e)))
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            failed += 1
            errors.append((name, str(e)))

    print(f"\n{'=' * 60}")
    print(f"결과: {passed} passed, {failed} failed, {skipped} skipped (총 {passed + failed + skipped})")

    if errors:
        print("\n실패한 테스트:")
        for name, err in errors:
            print(f"  - {name}: {err}")

    sys.exit(0 if failed == 0 else 1)
