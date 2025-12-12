import sys
import os

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager
from actions.file_editor import FileEditor
from actions.template_manager import TemplateManager
from actions.document_generator import DocumentGenerator
# AI 템플릿 어시스턴트 제거됨 (단순한 /new 명령어로 대체)
#from actions.ai_template_assistant import AITemplateAssistant
from cli.completer import PathCompleter
from llm.service import LLMService
from cli.core.context_manager import PromptBuilder
from cli.core.mcp_integration import MCPIntegration
from cli.core.debug_manager import DebugManager
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from cli.ui.components import SwingUIComponents
from cli.ui.panels import UIPanels
from cli.ui.formatters import ResponseFormatter
from cli.ui.interactive import InteractiveUI
from cli.ui.tutorial import TutorialMode
from cli.core.architect_mode import ArchitectMode

# 편집 전략 import
from cli.coders.base_coder import registry
from cli.coders import wholefile_coder, editblock_coder, udiff_coder

@click.command()
def main():
    """An interactive REPL for the Swing LLM assistant."""
    console = Console()
    ui = SwingUIComponents(console)
    panels = UIPanels(console)
    formatter = ResponseFormatter(console)
    interactive_ui = InteractiveUI(console)
    history = FileHistory('.swing-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    file_editor = FileEditor()
    llm_service = LLMService()
    template_manager = TemplateManager(llm_service=llm_service)
    document_generator = DocumentGenerator(console=console)
    # AI 어시스턴트 제거됨
    chat_history = []
    
    # AI 대화 상태 관리 - 제거됨 (단순한 /new 명령어로 대체)
    
    # 수정 의도 감지 시 자동 apply 플래그
    modification_auto_apply = False
    
    # 의도 분석 함수들 제거됨 (단순화)
    
    
    # MCP 통합 초기화
    mcp_integration = MCPIntegration()
    mcp_integration.initialize(console)
    task = 'ask'  # Default task
    edit_strategy = 'whole'  # 기본 편집 전략
    last_edit_response = None  # 마지막 edit 응답 저장
    last_user_request = None  # 마지막 사용자 요청 저장
    current_coder = registry.get_coder(edit_strategy, file_editor)  # 현재 코더 
    # 영구 PromptBuilder 인스턴스 (캐시 유지용)
    prompt_builder = PromptBuilder('ask')
    
    # Architect Mode 초기화 (템플릿 매니저 포함)
    architect_mode = ArchitectMode(console, llm_service, file_manager, file_editor, session, template_manager)

    # 웰컴 메시지
    interactive_ui.display_welcome_banner(task)

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.strip().lower() in ('/exit', '/quit'):
                console.print(panels.create_goodbye_panel())
                break

            elif user_input.strip().lower() == '/help':
                console.print(interactive_ui.display_help_panel())
                continue

            elif user_input.strip().lower() == '/tutorial':
                # Start tutorial mode
                console.print(interactive_ui.display_tutorial_start_panel())
                
                try:
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
                    tutorial.start()
                except Exception as e:
                    console.print(panels.create_error_panel(f"튜토리얼 실행 중 오류: {e}"))
                
                continue

            elif user_input.strip().lower().startswith('/architect '):
                # Architect Mode - AI 작업 오케스트레이션
                # 사용자 요청 추출 (/architect 뒤의 모든 내용)
                request = user_input.strip()[11:].strip()  # '/architect ' 접두사 제거
                
                if not request:
                    console.print(panels.create_error_panel("사용법: /architect \"자연어 요청\"\n예: /architect \"유선 회선 기준으로 유무선 결합 가입년수 합산값 조회하는 쿼리 개발해줘\""))
                    continue
                
                try:
                    # Architect 모드 실행
                    plan = architect_mode.run(request)
                    
                    if plan:
                        console.print(f"\n[bold green]✅ Architect Mode 완료![/bold green]")
                        console.print(f"[dim]계획 ID: {plan.plan_id}[/dim]")
                        console.print(f"[dim]상태: {plan.status}[/dim]")
                except Exception as e:
                    console.print(panels.create_error_panel(f"Architect Mode 실행 중 오류: {e}"))
                
                continue

            elif user_input.strip().lower() == '/resume':
                # Resume - List and resume saved plans
                try:
                    plan_ids = architect_mode.list_plans()
                    
                    if not plan_ids:
                        console.print("[yellow]저장된 계획이 없습니다.[/yellow]")
                        continue
                    
                    # Show available plans
                    console.print(Panel(
                        "[bold cyan]📋 저장된 계획 목록[/bold cyan]",
                        border_style="cyan"
                    ))
                    
                    for idx, plan_id in enumerate(plan_ids[:10], 1):
                        console.print(f"  {idx}. [cyan]{plan_id}[/cyan]")
                    
                    if len(plan_ids) > 10:
                        console.print(f"\n  [dim]... and {len(plan_ids) - 10} more plans[/dim]")
                    
                    # Ask user to select
                    console.print("\n[bold]계획을 선택하세요 (번호 입력):[/bold]")
                    choice = session.prompt("선택 > ")
                    
                    try:
                        idx = int(choice.strip())
                        if 1 <= idx <= min(10, len(plan_ids)):
                            selected_plan_id = plan_ids[idx - 1]
                            
                            # Load and show plan
                            plan = architect_mode.load_plan(selected_plan_id)
                            
                            if plan:
                                architect_mode.visualize_plan(plan)
                                
                                # Ask if user wants to re-execute
                                if Confirm.ask("\n이 계획을 다시 실행하시겠습니까?", default=False, console=console):
                                    architect_mode.execute_plan(plan)
                                    architect_mode.save_plan(plan)
                        else:
                            console.print("[red]잘못된 선택입니다.[/red]")
                    except ValueError:
                        console.print("[red]숫자를 입력해주세요.[/red]")
                        
                except Exception as e:
                    console.print(panels.create_error_panel(f"Resume 실행 중 오류: {e}"))
                
                continue

            elif user_input.strip().lower().startswith('/repo'):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    target_files = [p.replace('@', '') for p in parts[1:]]

                    # 수동으로 레포맵 생성
                    repo_map = prompt_builder.generate_repo_map_manually(target_files, file_manager)

                    if repo_map:
                        console.print(panels.create_repo_map_panel(repo_map))
                        console.print(f"•  RepoMap 생성 완료! '/ask' 명령시 자동으로 포함됩니다.")
                    else:
                        console.print("[red]•  RepoMap 생성에 실패했습니다.[/red]")
                else:
                    # 상태 확인
                    status = prompt_builder.get_repo_map_status()
                    console.print(f"[cyan]•  RepoMap 상태: {status}[/cyan]")
                    console.print("[dim]사용법: /repo <파일1> <파일2> ... 또는 /repo (상태 확인)[/dim]")
                continue

            elif user_input.strip().lower().startswith('/swmate-cache'):
                # SWMateAnalyzer 캐시 상태 확인
                parts = user_input.strip().split()
                if len(parts) == 1 or (len(parts) == 2 and parts[1] == 'status'):
                    # 캐시 상태 확인
                    status = prompt_builder.get_swmate_cache_status()
                    console.print(f"[cyan]•  SWMateAnalyzer 캐시 상태:[/cyan]")
                    console.print(status)
                    continue
                
            elif user_input.strip().lower() == 'swmate init':
                # 프로젝트 초기화 - AGENTS.md 문서 생성
                document_generator.init_project()
                continue

            elif user_input.strip().lower().startswith('/add '):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    result = file_manager.add(files_to_add)
                    
                    # 파일 추가 결과 표시 (UI 모듈로 이동)
                    interactive_ui.display_file_add_results(result, file_manager, ui, console)
                        
                else:
                    interactive_ui.display_command_results('/add', {'error': True, 'message': '사용법: /add <file1|dir1> <file2|dir2> ...'}, console)
                continue

            elif user_input.strip().lower() == '/files':
                console.print(ui.file_list_table(file_manager.files))
                continue

            elif user_input.strip().lower() == '/tree':
                if file_manager.files:
                    console.print(ui.file_tree(file_manager.files))
                else:
                    interactive_ui.display_command_results('/tree', {'message': "추가된 파일이 없습니다. '/add <파일경로>' 명령으로 파일을 추가하세요."}, console)
                continue


            elif user_input.strip().lower().startswith('/info '):
                parts = user_input.strip().split()
                if len(parts) > 1:
                    user_file_path = parts[1].replace('@', '')  # @ 제거
                    
                    # 여러 방식으로 파일 찾기 시도
                    found_file_path = None
                    
                    # 1. 입력 경로 그대로
                    if user_file_path in file_manager.files:
                        found_file_path = user_file_path
                    # 2. 절대 경로로 변환
                    elif not os.path.isabs(user_file_path):
                        abs_path = os.path.abspath(user_file_path)
                        if abs_path in file_manager.files:
                            found_file_path = abs_path
                    # 3. 파일명만으로 검색 (basename)
                    if not found_file_path:
                        input_basename = os.path.basename(user_file_path)
                        for file_path in file_manager.files.keys():
                            if os.path.basename(file_path) == input_basename:
                                found_file_path = file_path
                                break
                    # 4. 부분 경로 매칭
                    if not found_file_path:
                        for file_path in file_manager.files.keys():
                            if user_file_path in file_path or file_path.endswith(user_file_path):
                                found_file_path = file_path
                                break
                    
                    if found_file_path:
                        # 파일 분석 다시 수행
                        result = file_manager.add_single_file(found_file_path)
                        if result.get('analysis'):
                            analysis_result = ui.file_analysis_panel([
                                {
                                    'file_path': found_file_path,
                                    'file_type': result['file_type'],
                                    'analysis': result['analysis']
                                }
                            ])
                            if isinstance(analysis_result, list):
                                for panel in analysis_result:
                                    console.print(panel)
                                    console.print()
                            else:
                                console.print(analysis_result)
                        else:
                            interactive_ui.display_command_results('/info', {'message': f'파일 분석 정보가 없습니다: {os.path.basename(found_file_path)}'}, console)
                    else:
                        # 사용 가능한 파일들 표시
                        available_files = [os.path.basename(f) for f in file_manager.files.keys()]
                        message = f"파일을 찾을 수 없습니다: {user_file_path}\n\n사용 가능한 파일들:\n" + "\n".join(f"• {f}" for f in available_files[:10])
                        interactive_ui.display_command_results('/info', {'error': True, 'message': message}, console)
                else:
                    interactive_ui.display_command_results('/info', {'error': True, 'message': '사용법: /info @<file_path>'}, console)
                continue

            elif user_input.strip().lower() == '/session':
                session_id = llm_service.get_session_id()
                interactive_ui.display_session_info(session_id, console)
                continue

            elif user_input.strip().lower() == '/session-reset':
                llm_service.reset_session()
                interactive_ui.display_command_results('/session-reset', {'success': True, 'message': '세션이 초기화되었습니다.'}, console)
                continue

            elif user_input.strip().lower() == '/mcp':
                mcp_integration.show_mcp_status(console)
                continue

            elif user_input.strip().lower().startswith('/mcp help '):
                parts = user_input.strip().split()
                if len(parts) >= 3:
                    tool_name = ' '.join(parts[2:])
                    mcp_integration.show_tool_help(tool_name, console)
                else:
                    interactive_ui.display_command_results('/mcp', {'error': True, 'message': '사용법: /mcp help <도구명>'}, console)
                continue

            elif user_input.strip().lower() == '/clear':
                chat_history.clear()
                interactive_ui.display_command_results('/clear', {'success': True, 'message': '대화 기록이 초기화되었습니다.'}, console)
                continue

            elif user_input.strip().lower() == '/preview':
                if not last_edit_response:
                    interactive_ui.display_command_results('/preview', {'message': '미리볼 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요.'}, console)
                else:
                    preview = current_coder.preview_changes(last_edit_response, file_manager.files)
                    if 'error' in preview:
                        interactive_ui.display_command_results('/preview', {'error': True, 'message': f"{preview['error']['message']} (전략: {preview['error']['strategy']})"}, console)
                    else:
                        panels = ui.file_changes_preview(preview)
                        for panel in panels:
                            console.print(panel)
                continue

            elif user_input.strip().lower() == '/apply':
                if not last_edit_response:
                    interactive_ui.display_command_results('/apply', {'message': '적용할 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요.'}, console)
                else:
                    try:
                        # 더 구체적인 설명 생성
                        summary = current_coder.preview_changes(last_edit_response, file_manager.files)
                        if summary and 'error' not in summary:
                            file_names = list(summary.keys())
                            if len(file_names) == 1:
                                file_desc = f"{file_names[0]} 수정"
                            else:
                                file_desc = f"{len(file_names)}개 파일 수정"
                        else:
                            file_desc = "파일 수정"
                        
                        # 사용자 요청 내용 포함
                        if last_user_request and len(last_user_request) < 50:
                            description = f"{file_desc}: {last_user_request} ({edit_strategy})"
                        else:
                            description = f"{file_desc} ({edit_strategy} 전략)"
                        
                        operation = current_coder.apply_changes(last_edit_response, file_manager.files, description)
                        console.print(ui.apply_confirmation(len(operation.changes)))
                        
                        # 편집 요약 표시
                        summary = operation.get_summary()
                        console.print(ui.edit_summary_panel(summary))
                        
                        last_edit_response = None  # 적용 후 초기화
                    except Exception as e:
                        interactive_ui.display_command_results('/apply', {'error': True, 'message': f'파일 적용 중 오류 발생: {e}'}, console)
                continue

            elif user_input.strip().lower() == '/history':
                operations = file_editor.get_history(10)
                console.print(ui.edit_history_table(operations))
                continue

            elif user_input.strip().lower() == '/debug':
                if last_edit_response:
                    console.print(Panel(
                        f"[bold]현재 전략:[/bold] {edit_strategy}\n"
                        f"[bold]마지막 Edit 응답 원문:[/bold]\n\n{last_edit_response[:1000]}{'...' if len(last_edit_response) > 1000 else ''}",
                        title="🐛 디버그 정보",
                        style="yellow"
                    ))
                    
                    # 코더별 파싱 테스트
                    parsed = current_coder.parse_response(last_edit_response, file_manager.files)
                    console.print(Panel(
                        f"[bold]파싱 결과 ({edit_strategy}):[/bold]\n" +
                        (f"파일 {len(parsed)}개 감지: {list(parsed.keys())}" if parsed else "파싱된 파일 없음"),
                        title="📝 파싱 결과",
                        style="cyan"
                    ))
                else:
                    interactive_ui.display_command_results('/debug', {'message': '디버그할 edit 응답이 없습니다.'}, console)
                continue


            elif user_input.strip().lower().startswith('/rollback '):
                parts = user_input.strip().split()
                if len(parts) == 2:
                    operation_id = parts[1]
                    # 해당 작업 찾기
                    operations = file_editor.get_history()
                    target_op = None
                    for op in operations:
                        if op.operation_id == operation_id:
                            target_op = op
                            break
                    
                    if target_op:
                        console.print(ui.rollback_confirmation(operation_id, target_op.description))
                    else:
                        interactive_ui.display_command_results('/rollback', {'error': True, 'message': f"작업 ID '{operation_id}'를 찾을 수 없습니다."}, console)
                
                elif len(parts) == 3 and parts[1] != 'cancel':
                    operation_id, action = parts[1], parts[2]
                    if action == 'confirm':
                        try:
                            success = file_editor.rollback_operation(operation_id)
                            if success:
                                console.print(ui.rollback_success(operation_id))
                            else:
                                interactive_ui.display_command_results('/rollback', {'error': True, 'message': f"작업 '{operation_id}' 롤백에 실패했습니다."}, console)
                        except Exception as e:
                            interactive_ui.display_command_results('/rollback', {'error': True, 'message': f'롤백 중 오류 발생: {e}'}, console)
                    else:
                        interactive_ui.display_command_results('/rollback', {'error': True, 'message': "'/rollback <ID> confirm' 형식으로 입력하세요."}, console)
                
                elif len(parts) == 2 and parts[1] == 'cancel':
                    interactive_ui.display_command_results('/rollback', {'success': True, 'message': '롤백이 취소되었습니다.'}, console)
                
                else:
                    interactive_ui.display_command_results('/rollback', {'error': True, 'message': '사용법: /rollback <ID> 또는 /rollback <ID> confirm'}, console)
                continue

            elif user_input.strip().lower() == '/ask':
                task = 'ask'
                interactive_ui.display_mode_switch_message(task)
                continue

            elif user_input.strip().lower() == '/new':
                # 간단한 파일 생성 명령어
                templates = template_manager.list_templates()
                if not templates:
                    console.print(panels.create_error_panel("templates/ 디렉토리에 템플릿 파일이 없습니다."))
                    continue

                # 템플릿 목록 표시
                table = template_manager.display_templates_table()
                console.print(table)
                console.print()

                try:
                    # 템플릿 선택
                    template_choice = session.prompt("템플릿 번호를 선택하세요: ").strip()
                    if not template_choice.isdigit():
                        console.print(panels.create_error_panel("올바른 숫자를 입력하세요."))
                        continue

                    template_num = int(template_choice)
                    if not (1 <= template_num <= len(templates)):
                        console.print(panels.create_error_panel(f"1-{len(templates)} 범위의 숫자를 입력하세요."))
                        continue

                    # 서비스 정보 입력
                    service_id = session.prompt("서비스 ID (예: EDUSS0100101T01): ").strip()
                    if not service_id:
                        console.print(panels.create_error_panel("서비스 ID는 필수입니다."))
                        continue

                    filename = session.prompt("파일명 (예: eduss0100101t01): ").strip()
                    if not filename:
                        console.print(panels.create_error_panel("파일명은 필수입니다."))
                        continue

                    description = session.prompt("설명 (선택사항): ").strip()

                    # 파일 생성
                    template_name = templates[template_num - 1]["name"]
                    success = template_manager.create_from_template(
                        template_name, service_id, f"{filename}.c", "user", description
                    )

                    if success:
                        actual_path = os.path.join("SWING_AUTO_FILES", f"{filename}.c")
                        console.print(panels.create_success_panel(
                            f"✅ 파일 생성 완료: {actual_path}\n"
                            f"서비스 ID: {service_id}\n"
                            f"설명: {description or '없음'}",
                            "파일 생성 완료"
                        ))
                    else:
                        console.print(panels.create_error_panel("파일 생성에 실패했습니다."))

                except (KeyboardInterrupt, EOFError):
                    console.print(panels.create_warning_panel("파일 생성이 취소되었습니다."))
                continue

            elif user_input.strip().lower().startswith('/edit'):
                parts = user_input.strip().split()
                if len(parts) == 1:
                    # 기본 edit 모드
                    task = 'edit'
                    interactive_ui.display_mode_switch_message(task)
                elif len(parts) == 2:
                    # 전략과 함께 edit 모드
                    strategy_name = parts[1].lower()
                    if strategy_name in registry._coders:
                        edit_strategy = strategy_name
                        current_coder = registry.get_coder(edit_strategy, file_editor)
                        task = 'edit'
                        console.print(f"[bold green]✅ '{strategy_name}' 전략으로 edit 모드가 설정되었습니다.[/bold green]")
                        console.print(f"[dim]✏️ 이제 {strategy_name} 방식으로 코드 수정을 요청할 수 있습니다.[/dim]\n")
                    else:
                        available = list(registry._coders.keys())
                        interactive_ui.display_command_results('/edit', {'error': True, 'message': f"알 수 없는 전략: {strategy_name}\n사용 가능: {', '.join(available)}"}, console)
                else:
                    interactive_ui.display_command_results('/edit', {'error': True, 'message': '사용법: /edit 또는 /edit <전략명> (예: /edit udiff)'}, console)
                continue

            elif user_input.strip() == "":
                continue

            # AI 대화 상태 처리 - 제거됨 (/new 명령어로 대체)

            # "수정해줘" 등 edit 요청 키워드 감지 시 edit 모드로 자동 전환
            elif any(keyword in user_input for keyword in ["수정해줘", "수정해 줘", "바꿔줘", "바꿔 줘", "고쳐줘", "고쳐 줘", "편집해줘", "편집해 줘"]):
                if task != 'edit':
                    task = 'edit'
                    console.print(f"[bold green]✅ '수정해줘' 요청으로 edit 모드로 자동 전환되었습니다.[/bold green]")
                    console.print(f"[dim]✏️ 이제 파일 수정을 요청할 수 있습니다.[/dim]\n")
                
                # edit 모드에서 처리하도록 계속 진행
                interactive_ui.display_separator()
                # 사용자 입력 패널 제거 (사용자 요청)

            # 잘못된 명령어 처리 (/ 로 시작하지만 알려진 명령어가 아닌 경우)
            elif user_input.startswith('/'):
                known_commands = ['/add', '/files', '/tree', '/info', '/clear', '/preview', '/apply',
                                '/history', '/debug', '/rollback', '/ask', '/edit', '/new', '/session', '/session-reset', '/mcp', '/repo', '/help', '/exit', '/quit', '/swmate-cache', '/tutorial', '/architect', '/resume']
                
                # 명령어 부분만 추출 (공백 전까지)
                command_part = user_input.split()[0].lower()
                
                if command_part not in known_commands:
                    interactive_ui.display_unknown_command_error(command_part)
                    continue

            else:
                # 의도 분석 제거됨 - 직접 ask 모드 처리

                # 일반 사용자 입력 - AI에게 전달 (의도 분석 없이 바로 처리)
                interactive_ui.display_separator()

            # Build the prompt using persistent PromptBuilder (캐시 유지)
            prompt_builder.set_task(task)  # task 모드만 변경 (캐시는 유지)
            messages = prompt_builder.build(user_input, file_manager.files, chat_history, file_manager)

            # 입출력 관련 질문인지 확인하고 JSON 강제 모드 사용
            force_json = hasattr(prompt_builder, 'is_io_question') and prompt_builder.is_io_question
            
            # 로딩 메시지
            with interactive_ui.display_loading_message():
                llm_response = llm_service.chat_completion(messages, force_json=force_json)

            if llm_response and "choices" in llm_response:
                llm_message = llm_response["choices"][0]["message"]
                response_content = llm_message['content']
                
                # DEBUG: LLM 응답 정보 표시
                DebugManager.llm(f"LLM 응답 길이: {len(response_content)}")
                DebugManager.llm(f"LLM 응답 미리보기: {response_content[:200]}...")
                #DebugManager.llm(f"JSON 강제 모드: {force_json}")
                
                # MCP 도구 호출 처리
                mcp_result = mcp_integration.process_llm_response(response_content, user_input)
                if mcp_result.get('has_tool_calls'):
                    # MCP 도구 호출 시 LLM 응답은 디버그로만 표시
                    DebugManager.llm(f"LLM 원본 응답: {response_content[:100]}...")
                    
                    # LLM이 자연스럽게 변환한 답변을 AI Response로 표시
                    natural_response = mcp_result.get('natural_response', '응답을 생성할 수 없습니다.')
                    console.print(panels.create_ai_response_panel(natural_response))
                # MCP 도구 호출이 없는 경우 - 원래 응답 처리 로직 실행
                elif task == 'edit':
                    # Edit 모드: 코드 생성 응답 표시
                    # console.print(ui.edit_mode_response_panel(response_content))
                    
                    # 마지막 edit 응답과 사용자 요청 저장
                    last_edit_response = response_content
                    last_user_request = user_input
                    
                    # 자동으로 미리보기 표시
                    try:
                        preview = current_coder.preview_changes(response_content, file_manager.files)
                        if preview and 'error' not in preview:
                            console.print()
                            panels = ui.file_changes_preview(preview)
                            for panel in panels:
                                console.print(panel)
                            
                            console.print()
                            
                            # 수정 의도 감지로 edit 모드가 된 경우 자동으로 apply 여부 묻기
                            if modification_auto_apply:
                                console.print(f"[bold cyan]💡 수정사항을 실제 파일에 적용하시겠습니까?[/bold cyan]")
                                apply_confirm = session.prompt("적용하시겠습니까? (y/n): ").strip().lower()
                                if apply_confirm in ['y', 'yes', '네', 'ㅇ']:
                                    # /apply 명령 실행
                                    apply_result = current_coder.apply_changes(last_edit_response, file_manager.files)
                                    if apply_result.get('success'):
                                        message = f"변경사항이 적용되었습니다.\n\n적용된 파일:\n" + '\n'.join(f"• {file}" for file in apply_result.get('applied_files', []))
                                        interactive_ui.display_command_results('auto-apply', {'success': True, 'message': message}, console)
                                        
                                        # 적용된 파일들을 파일 매니저에 다시 로드
                                        for file_path in apply_result.get('applied_files', []):
                                            if file_path in file_manager.files:
                                                file_manager.reload_file(file_path)
                                    else:
                                        interactive_ui.display_command_results('auto-apply', {'error': True, 'message': apply_result.get('error', '알 수 없는 오류')}, console)
                                else:
                                    console.print(f"[dim]변경사항이 적용되지 않았습니다. 나중에 /apply 명령으로 적용할 수 있습니다.[/dim]")
                                
                                modification_auto_apply = False  # 플래그 리셋
                            else:
                                interactive_ui.display_edit_next_steps()
                        elif preview and 'error' in preview:
                            interactive_ui.display_command_results('edit-preview', {'error': True, 'message': f"{preview['error']['message']} (전략: {preview['error']['strategy']})"}, console)
                    except Exception as e:
                        interactive_ui.display_command_results('edit-preview', {'message': f'미리보기 생성 중 오류: {e}'}, console)
                    
                    # Edit 후 자동으로 파일 분석 수행
                    if preview and 'error' not in preview and preview:
                        console.print("\n[bold blue]🔍 수정된 파일에 대한 자동 분석을 수행합니다...[/bold blue]")
                        try:
                            from cli.core.analyzer import CoeAnalyzer
                            analyzer = CoeAnalyzer()
                            
                            # 수정될 파일들 추출
                            modified_files = list(preview.keys())
                            
                            if modified_files:
                                llm_results = analyzer._perform_llm_analysis(
                                    {f: {'file_type': 'unknown', 'basic_analysis': {}}}
                                     for f in modified_files if f in file_manager.files
                                )
                                
                                # 분석 결과 요약 표시
                                if llm_results:
                                    console.print()
                                    for file_path, llm_analysis in llm_results.items():
                                        if llm_analysis.get('purpose'):
                                            filename = os.path.basename(file_path)
                                            summary_text = f"수정 후 예상 결과: {llm_analysis.get('purpose', 'N/A')}"
                                            
                                            console.print(f"[dim]📊 {filename}: {summary_text}[/dim]")
                        except Exception as e:
                            pass  # 자동 분석 실패는 조용히 넘어감
                else:
                    # Ask 모드: 응답 처리
                    formatted = formatter.format_json_response(response_content, force_json)
                    if formatted is None:
                        console.print(panels.create_ai_response_panel(response_content))


                # Add user input and LLM response to history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_content})
            else:
                console.print(panels.create_error_panel("AI가 응답을 생성하지 못했습니다."))
            
            console.print()  # 빈 줄 추가

        except KeyboardInterrupt:
            console.print(panels.create_warning_panel("작업이 중단되었습니다."))
            continue
        except EOFError:
            console.print(panels.create_goodbye_panel())
            break
        except ValueError as e:
            console.print(panels.create_error_panel(str(e), "입력 오류"))
            continue


if __name__ == '__main__':
    main()
