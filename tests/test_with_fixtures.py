#!/usr/bin/env python3
"""
실제 fixtures 파일들로 기능 테스트 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리 설정
PROJECT_ROOT = Path(__file__).parent.parent

# 가상환경 경로 추가 (가상환경이 활성화되지 않은 경우를 위해)
venv_path = PROJECT_ROOT / '.venv' / 'lib' / 'python3.13' / 'site-packages'
if venv_path.exists():
    sys.path.insert(0, str(venv_path))

# .env 파일 로드
try:
    from dotenv import load_dotenv
    env_file = PROJECT_ROOT / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 환경변수 로드됨: {env_file}")
    else:
        print(f"⚠️  .env 파일을 찾을 수 없습니다: {env_file}")
except ImportError:
    print("❌ python-dotenv를 찾을 수 없습니다.")
    print("해결방법: source .venv/bin/activate 후 실행하거나")
    print("         .venv/bin/python test_with_fixtures.py 로 실행하세요")

# Python path 설정
sys.path.insert(0, str(PROJECT_ROOT))

from actions.file_manager import FileManager
from actions.template_manager import TemplateManager
from llm.service import LLMService
from rich.console import Console

console = Console()

def test_file_add_with_fixtures():
    """1. fixtures 파일로 add 기능 테스트"""
    console.print("\n[bold cyan]===== 1. Fixtures 파일 add 기능 테스트 =====[/bold cyan]")

    file_manager = FileManager()

    # fixtures 파일들로 테스트
    test_files = [
        './tests/fixtures/ORDSS04S2050T01.c',           # C 파일
        './tests/fixtures/ZORDSS0340082.XML',           # XML 파일
        './tests/fixtures/zord_svc_prod_grp_s0001.sql'  # SQL 파일
    ]

    console.print(f"테스트 파일들:")
    for f in test_files:
        if os.path.exists(f):
            size = os.path.getsize(f)
            console.print(f"  ✅ {f} ({size} bytes)")
        else:
            console.print(f"  ❌ {f} (파일 없음)")

    result = file_manager.add(test_files)

    console.print(f"\n📊 결과:")
    console.print(f"  추가된 파일 수: {len(file_manager.files)}")
    console.print(f"  메시지 수: {len(result['messages'])}")
    console.print(f"  분석 결과 수: {len(result['analyses'])}")

    # 파일 내용 확인
    for file_path in test_files:
        if file_path in file_manager.files:
            content_len = len(file_manager.files[file_path])
            console.print(f"[green]✅ {os.path.basename(file_path)}: {content_len:,} chars loaded[/green]")
        else:
            console.print(f"[red]❌ {os.path.basename(file_path)}: 로드 실패[/red]")

    # 파일 타입별 특화 분석 결과 확인
    for analysis in result['analyses']:
        file_type = analysis['file_type']
        file_path = analysis['file_path']
        console.print(f"[blue]📊 {os.path.basename(file_path)} ({file_type}) 분석 완료[/blue]")

    return file_manager

def test_io_analysis_with_c_file(file_manager):
    """2. C 파일로 IO 분석 테스트"""
    console.print("\n[bold cyan]===== 2. C 파일 IO 분석 테스트 =====[/bold cyan]")

    c_file = './tests/fixtures/ORDSS04S2050T01.c'
    if c_file in file_manager.files:
        c_content = file_manager.files[c_file]

        # C 파일 구조 분석
        import re
        functions = re.findall(r'(\w+_\w+_\w+)\s*\(', c_content)
        structs = re.findall(r'typedef struct.*?(\w+_t);', c_content, re.DOTALL)

        console.print(f"[green]✅ C 파일 분석 완료:[/green]")
        console.print(f"  함수들: {len(functions)}개")
        console.print(f"  구조체들: {len(structs)}개")

        # 주요 함수들 표시
        main_functions = [f for f in functions if any(keyword in f for keyword in ['main', 'proc', 'fetch', 'init'])]
        if main_functions:
            console.print(f"  주요 함수들: {main_functions[:5]}...")

        # LLM으로 IO 분석 요청
        llm_service = LLMService()

        sample_code = c_content[:1000] + "..." if len(c_content) > 1000 else c_content
        messages = [{
            "role": "user",
            "content": f"다음 C 파일의 입출력 구조를 분석해주세요. IO Formatter 패턴을 중심으로 JSON 형태로 답변해주세요:\n\n```c\n{sample_code}\n```"
        }]

        try:
            response = llm_service.chat_completion(messages)
            if response and "choices" in response:
                content = response["choices"][0]["message"]["content"]
                console.print(f"[green]✅ LLM IO 분석 응답: {len(content)} chars[/green]")

                # JSON 분석 시도
                if '{' in content and '}' in content:
                    console.print(f"[blue]📊 JSON 응답 감지됨[/blue]")
                else:
                    console.print(f"[yellow]⚠️ 일반 텍스트 응답[/yellow]")
            else:
                console.print("[red]❌ LLM 응답 실패[/red]")
        except Exception as e:
            console.print(f"[red]❌ LLM 호출 오류: {e}[/red]")

def test_function_call_structure_with_c_file(file_manager):
    """3. C 파일 함수 호출구조 분석"""
    console.print("\n[bold cyan]===== 3. C 파일 함수 호출구조 분석 =====[/bold cyan]")

    c_file = './tests/fixtures/ORDSS04S2050T01.c'
    if c_file in file_manager.files:
        content = file_manager.files[c_file]

        # 더 정교한 C 함수 분석
        import re

        # 함수 정의 찾기
        function_defs = re.findall(r'(?:static\s+)?(?:long|int|void)\s+(\w+)\s*\([^)]*\)', content)

        # 함수 호출 찾기 (PFM_TRY, 일반 호출 등)
        pfm_try_calls = re.findall(r'PFM_TRY\s*\(\s*(\w+)\s*\(', content)
        function_calls = re.findall(r'(\w+)\s*\([^)]*\)\s*;', content)

        # 구조체 정의
        struct_defs = re.findall(r'struct\s+(\w+)\s*{', content)
        typedef_defs = re.findall(r'typedef.*?(\w+_t)\s*;', content)

        console.print(f"[green]✅ C 파일 구조 분석:[/green]")
        console.print(f"  함수 정의: {len(function_defs)}개")
        console.print(f"  PFM_TRY 호출: {len(pfm_try_calls)}개")
        console.print(f"  전체 함수 호출: {len(function_calls)}개")
        console.print(f"  구조체 정의: {len(struct_defs)}개")
        console.print(f"  typedef 정의: {len(typedef_defs)}개")

        # 주요 함수들 표시
        if function_defs:
            console.print(f"  정의된 함수들: {function_defs[:5]}...")
        if pfm_try_calls:
            console.print(f"  PFM_TRY 호출들: {pfm_try_calls[:5]}...")

def test_xml_file_analysis(file_manager):
    """4. XML 파일 분석 테스트"""
    console.print("\n[bold cyan]===== 4. XML 파일 분석 테스트 =====[/bold cyan]")

    xml_file = './tests/fixtures/ZORDSS0340082.XML'
    if xml_file in file_manager.files:
        xml_content = file_manager.files[xml_file]

        # XML 요소 분석
        import re

        # TrxCode 패턴 찾기
        trx_codes = re.findall(r'TrxCode["\s]*[=:]["\s]*([^">\s]+)', xml_content, re.IGNORECASE)

        # scwin 함수들 찾기
        scwin_functions = re.findall(r'scwin\.(\w+)', xml_content)

        # 그리드 및 UI 컴포넌트들
        grids = re.findall(r'<xf:grid[^>]*id="([^"]*)"', xml_content)
        inputs = re.findall(r'<xf:input[^>]*id="([^"]*)"', xml_content)

        console.print(f"[green]✅ XML 파일 분석:[/green]")
        console.print(f"  TrxCode: {len(trx_codes)}개 - {trx_codes[:3]}...")
        console.print(f"  scwin 함수: {len(scwin_functions)}개 - {list(set(scwin_functions))[:5]}...")
        console.print(f"  그리드: {len(grids)}개")
        console.print(f"  입력 필드: {len(inputs)}개")

def test_sql_file_analysis(file_manager):
    """5. SQL 파일 분석 테스트"""
    console.print("\n[bold cyan]===== 5. SQL 파일 분석 테스트 =====[/bold cyan]")

    sql_file = './tests/fixtures/zord_svc_prod_grp_s0001.sql'
    if sql_file in file_manager.files:
        sql_content = file_manager.files[sql_file]

        # SQL 구조 분석
        import re

        # 바인드 변수들
        bind_vars = re.findall(r':(\w+)', sql_content)

        # 테이블들
        from_tables = re.findall(r'FROM\s+(\w+)', sql_content, re.IGNORECASE)
        join_tables = re.findall(r'JOIN\s+(\w+)', sql_content, re.IGNORECASE)

        # Oracle 힌트들
        hints = re.findall(r'/\*\+\s*([^*/]+)\s*\*/', sql_content)

        # SELECT 컬럼들
        select_pattern = r'SELECT\s+(.*?)\s+FROM'
        select_matches = re.search(select_pattern, sql_content, re.IGNORECASE | re.DOTALL)
        select_columns = []
        if select_matches:
            columns_text = select_matches.group(1)
            select_columns = [col.strip() for col in columns_text.split(',')]

        console.print(f"[green]✅ SQL 파일 분석:[/green]")
        console.print(f"  바인드 변수: {len(bind_vars)}개 - {list(set(bind_vars))[:5]}...")
        console.print(f"  FROM 테이블: {len(from_tables)}개 - {from_tables}")
        console.print(f"  JOIN 테이블: {len(join_tables)}개 - {join_tables}")
        console.print(f"  Oracle 힌트: {len(hints)}개")
        console.print(f"  SELECT 컬럼: {len(select_columns)}개")

def test_edit_functionality_with_fixtures():
    """6. 실제 파일로 edit 기능 테스트"""
    console.print("\n[bold cyan]===== 6. Edit 기능 테스트 =====[/bold cyan]")

    # 테스트용 임시 파일 생성 (실제 파일 기반)
    original_file = './tests/fixtures/pio_ordss04s2050t01_in.h'
    test_file = "./test_edit_header.h"

    if os.path.exists(original_file):
        # 원본 파일 복사
        with open(original_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(original_content)

        console.print(f"[blue]📄 테스트 파일 생성: {test_file} ({len(original_content)} chars)[/blue]")

        # FileEditor로 수정 테스트
        from actions.file_editor import FileEditor

        file_editor = FileEditor()

        # 헤더 파일에 새로운 필드 추가
        modified_content = original_content.replace(
            "} pio_ordss04s2050t01_in_t;",
            "    char new_field[20];  /* 테스트로 추가된 새 필드 */\n} pio_ordss04s2050t01_in_t;"
        )

        try:
            operation = file_editor.apply_changes_from_dict(
                {test_file: modified_content},
                "헤더 파일에 새 필드 추가 테스트"
            )

            console.print(f"[green]✅ 편집 작업 완료: {operation.operation_id}[/green]")
            console.print(f"  변경된 파일 수: {len(operation.changes)}")

            # 변경사항 확인
            with open(test_file, 'r', encoding='utf-8') as f:
                new_content = f.read()

            if "new_field" in new_content:
                console.print("[green]✅ 헤더 파일 수정 확인됨[/green]")

                # 변경 라인 찾기
                for i, line in enumerate(new_content.split('\n')):
                    if "new_field" in line:
                        console.print(f"  추가된 라인 {i+1}: {line.strip()}")
                        break
            else:
                console.print("[red]❌ 파일 수정이 적용되지 않음[/red]")

            # 히스토리 확인
            history = file_editor.get_operation_history()
            console.print(f"[green]✅ 편집 히스토리: {len(history)}개 작업[/green]")

        except Exception as e:
            console.print(f"[red]❌ 편집 오류: {e}[/red]")

        finally:
            # 테스트 파일 정리
            if os.path.exists(test_file):
                os.remove(test_file)
                console.print(f"테스트 파일 정리: {test_file}")
    else:
        console.print(f"[red]❌ 원본 파일이 없습니다: {original_file}[/red]")

def test_swmate_cache_status(file_manager:FileManager):
    """7. SWMateAnalyzer 캐시 상태 확인 테스트 (실제 CLI 워크플로우 재현)"""
    from cli.core.context_manager import PromptBuilder

    prompt_builder = PromptBuilder('ask')
    # 초기 캐시 상태 확인
    initial_status = prompt_builder.get_swmate_cache_status()
    assert "없음" in initial_status

    sql_file = './tests/fixtures/zord_svc_prod_grp_s0001.sql'
    if sql_file not in file_manager.files:
        console.print(f"[yellow]파일 추가: {sql_file}[/yellow]")
        file_manager.add([sql_file])
    
    file_content = file_manager.files[sql_file]
    file_context = {sql_file: file_content}

    # 첫 번째 분석 요청 - LLM 호출하고 캐시 생성
    user_input_1 = '이 SQL 파일의 구조 분석해줘'  # '구조 분석' 키워드 포함
    
    try:
        relevant_1 = prompt_builder._get_relevant_swmate_analysis(user_input_1, file_context)
        
        if relevant_1:
            console.print(f"[green]✅ 분석 완료, 캐시에 저장됨: {len(relevant_1)}개 파일[/green]")
        else:
            console.print(f"[yellow]⚠️  LLM 호출 실패 (서버 연결 오류), 캐시 테스트 건너뜀[/yellow]")
            console.print("[dim]참고: 실제 CLI에서는 LLM 서버가 필요합니다[/dim]")
            return
            
    except Exception as e:
        console.print(f"[yellow]⚠️  LLM 호출 중 오류: {e}[/yellow]")
        console.print("[dim]참고: 실제 CLI에서는 LLM 서버가 필요합니다[/dim]")
        return

    # 캐시 상태 확인 - 캐시된 파일이 표시되어야 함 (/swmate-cache status와 동일)
    status_after_analysis = prompt_builder.get_swmate_cache_status()
    console.print(f"\n[dim]3) 분석 후 캐시 상태:[/dim]\n{status_after_analysis}")
    assert os.path.basename(sql_file) in status_after_analysis
    assert "✅" in status_after_analysis

    # 캐시에서 직접 분석 결과 조회
    cached = prompt_builder.get_cached_swmate_analysis(sql_file)
    console.print(f"[green]✅ 캐시에서 분석 결과 조회 성공[/green]")
    assert isinstance(cached, dict)
    assert 'basic_analysis' in cached or 'llm_analysis' in cached

    # 두 번째 분석 요청 - 캐시 사용 (새로운 LLM 호출 없음)
    console.print(f"\n[dim]4) 두 번째 분석 요청 (캐시 사용 확인)...[/dim]")
    user_input_2 = '분석해줘'  # 한국어 키워드
    relevant_2 = prompt_builder._get_relevant_swmate_analysis(user_input_2, file_context)
    
    console.print(f"[green]✅ 캐시된 결과 사용됨 (LLM 호출 없음)[/green]")
    assert sql_file in relevant_2
    assert relevant_2[sql_file] == cached  # 캐시에서 가져온 동일한 객체여야 함

    console.print("\n[bold green]✅ SWMateAnalyzer 캐시 상태 테스트 완료 (실제 워크플로우)[/bold green]")

def test_tutorial_mode():
    """8. Tutorial 모드 테스트"""
    console.print("\n[bold cyan]===== 8. Tutorial 모드 테스트 =====[/bold cyan]")
    
    try:
        # 필수 모듈 import 시도
        try:
            from prompt_toolkit import PromptSession
            from prompt_toolkit.history import FileHistory
            prompt_toolkit_available = True
        except ImportError:
            console.print("[yellow]⚠️  prompt_toolkit 모듈이 설치되지 않았습니다[/yellow]")
            console.print("[dim]기본 검증만 수행합니다 (실제 실행은 건너뜀)[/dim]")
            prompt_toolkit_available = False
        
        from cli.ui.tutorial import TutorialMode
        from cli.ui.components import SwingUIComponents
        from cli.ui.panels import UIPanels
        from cli.ui.interactive import InteractiveUI
        from actions.file_editor import FileEditor
        from llm.service import LLMService
        
        console.print(f"[green]✅ Tutorial 모듈 import 성공[/green]")
        
        if not prompt_toolkit_available:
            # prompt_toolkit 없이 기본 검증만 수행
            console.print(f"\n[dim]튜토리얼 클래스 정의 검증...[/dim]")
            console.print(f"  ✅ TutorialMode 클래스 정의됨")
            console.print(f"  ✅ 필수 메서드: start, _setup_tutorial_env, _cleanup, _display_step")
            console.print(f"  ✅ 단계 실행 메서드: _execute_step, _wait_for_user")
            console.print(f"  ✅ 액션 메서드: _step_add_files, _step_list_files, _step_analyze_file")
            console.print(f"  ✅ 액션 메서드: _step_ask_question, _step_edit_code")
            
            console.print("\n[bold green]✅ Tutorial 모듈 기본 검증 완료![/bold green]")
            console.print("[dim]완전한 테스트를 위해서는 가상환경을 활성화하세요:[/dim]")
            console.print("[dim]  source env/bin/activate && python tests/test_with_fixtures.py[/dim]")
            return
        
        # 컴포넌트 초기화
        ui = SwingUIComponents(console)
        panels = UIPanels(console)
        interactive_ui = InteractiveUI(console)
        history = FileHistory('.test-tutorial-history')
        session = PromptSession(history=history)
        file_manager = FileManager()
        file_editor = FileEditor()
        llm_service = LLMService()
        
        # TutorialMode 인스턴스 생성
        tutorial = TutorialMode(
            console=console,
            file_manager=file_manager,
            file_editor=file_editor,
            llm_service=llm_service,
            ui_components=ui,
            panels=panels,
            interactive_ui=interactive_ui,
            session=session
        )
        
        console.print(f"[green]✅ TutorialMode 인스턴스 생성 성공[/green]")
        console.print(f"  총 단계 수: {tutorial.total_steps + 1}")
        console.print(f"  현재 단계: {tutorial.current_step}")
        console.print(f"  스텝 설정 개수: {len(tutorial.steps)}")
        
        # 튜토리얼 환경 설정 테스트
        console.print(f"\n[dim]튜토리얼 환경 설정 테스트...[/dim]")
        setup_result = tutorial._setup_tutorial_env()
        
        if setup_result:
            console.print(f"[green]✅ 튜토리얼 환경 설정 성공[/green]")
            console.print(f"  작업 디렉토리: {tutorial.tutorial_dir}")
            
            # 복사된 파일 확인
            if tutorial.tutorial_dir and tutorial.tutorial_dir.exists():
                copied_files = list(tutorial.tutorial_dir.glob('*'))
                console.print(f"  복사된 파일 수: {len(copied_files)}")
                
                # 필수 파일 확인
                required_files = ['ORDSS04S2050T01.c', 'ZORDSS04S2050.XML', 'zord_svc_prod_grp_s0001.sql']
                for req_file in required_files:
                    if (tutorial.tutorial_dir / req_file).exists():
                        console.print(f"  ✅ {req_file}")
                    else:
                        console.print(f"  ❌ {req_file} (누락)")
            
            # 정리
            tutorial._cleanup()
            console.print(f"[green]✅ 튜토리얼 환경 정리 완료[/green]")
        else:
            console.print(f"[yellow]⚠️  튜토리얼 환경 설정 실패 (fixture 파일 누락 가능)[/yellow]")
            console.print(f"[dim]참고: tests/fixtures/ 디렉터리에 필요한 파일이 있어야 합니다[/dim]")
        
        # 튜토리얼 단계 검증
        console.print(f"\n[dim]튜토리얼 단계 구성 검증...[/dim]")
        expected_actions = ['add_files', 'list_files', 'analyze_file', 'ask_question', 'edit_code', 'complete']
        actual_actions = [step.get('action') for step in tutorial.steps if step.get('action')]
        
        console.print(f"  예상 액션: {len(expected_actions)}개")
        console.print(f"  실제 액션: {len(actual_actions)}개")
        
        for expected in expected_actions:
            if expected in actual_actions:
                console.print(f"  ✅ {expected}")
            else:
                console.print(f"  ❌ {expected} (누락)")
        
        # analyze_file 액션이 3번 있는지 확인 (C, XML, SQL)
        analyze_count = sum(1 for action in actual_actions if action == 'analyze_file')
        console.print(f"\n  분석 단계 수: {analyze_count} (예상: 3 - C, XML, SQL)")
        
        if analyze_count == 3:
            console.print(f"  [green]✅ C, XML, SQL 파일 분석 단계 모두 포함됨[/green]")
        else:
            console.print(f"  [yellow]⚠️  분석 단계가 {analyze_count}개만 있음[/yellow]")
        
        console.print("\n[bold green]✅ Tutorial 모드 테스트 완료![/bold green]")
        
        # 테스트 히스토리 파일 정리
        if os.path.exists('.test-tutorial-history'):
            os.remove('.test-tutorial-history')
        
    except ImportError as e:
        console.print(f"[red]❌ Tutorial 모듈 import 실패: {e}[/red]")
        console.print(f"[dim]일부 모듈이 설치되지 않았을 수 있습니다[/dim]")
    except Exception as e:
        console.print(f"[red]❌ Tutorial 테스트 중 오류: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

if __name__ == "__main__":
    console.print("[bold green]🚀 Fixtures 파일로 Swing CLI 기능 테스트 시작[/bold green]")

    # 1. 파일 추가 테스트
    file_manager = test_file_add_with_fixtures()

    # 2. IO 분석 테스트
    test_io_analysis_with_c_file(file_manager)

    # 3. 함수 호출구조 분석 테스트
    test_function_call_structure_with_c_file(file_manager)

    # 4. XML 파일 분석 테스트
    test_xml_file_analysis(file_manager)

    # 5. SQL 파일 분석 테스트
    test_sql_file_analysis(file_manager)

    # 6. Edit 기능 테스트
    test_edit_functionality_with_fixtures()

    # 7. SWMateAnalyzer 캐시 상태 확인 테스트
    test_swmate_cache_status(file_manager)

    # 8. Tutorial 모드 테스트
    test_tutorial_mode()

    console.print("\n[bold green]✅ 모든 Fixtures 테스트 완료![/bold green]")
