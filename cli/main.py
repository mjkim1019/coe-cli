import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager
from actions.file_editor import FileEditor
from cli.completer import PathCompleter
from llm.service import LLMService
from cli.core.context_manager import PromptBuilder
from rich.console import Console
from rich.panel import Panel
from cli.ui.components import SwingUIComponents

# 편집 전략 import
from cli.coders.base_coder import registry
from cli.coders import wholefile_coder, editblock_coder, udiff_coder

@click.command()
def main():
    """An interactive REPL for the Swing LLM assistant."""
    console = Console()
    ui = SwingUIComponents(console)
    history = FileHistory('.swing-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    file_editor = FileEditor()
    llm_service = LLMService()
    chat_history = []
    task = 'ask'  # Default task
    edit_strategy = 'whole'  # 기본 편집 전략
    last_edit_response = None  # 마지막 edit 응답 저장
    last_user_request = None  # 마지막 사용자 요청 저장
    current_coder = registry.get_coder(edit_strategy, file_editor)  # 현재 코더

    # 웰컴 메시지
    ui.welcome_banner(task)

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.lower() in ('/exit', '/quit'):
                console.print(ui.goodbye_panel())
                break

            elif user_input.lower() == '/help':
                console.print(ui.help_panel())
                continue

            elif user_input.lower().startswith('/add '):
                parts = user_input.split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    result = file_manager.add(files_to_add)
                    
                    # 기본 추가 메시지 표시
                    if isinstance(result, dict) and 'messages' in result:
                        console.print(ui.file_added_panel("\n".join(result['messages'])))
                        
                        # 파일 분석 결과가 있으면 추가로 표시
                        if result.get('analyses'):
                            analysis_result = ui.file_analysis_panel(result['analyses'])
                            if analysis_result:
                                console.print()
                                # 결과가 리스트인 경우 (테이블 포함)
                                if isinstance(analysis_result, list):
                                    for panel in analysis_result:
                                        console.print(panel)
                                        console.print()
                                else:
                                    console.print(analysis_result)
                    else:
                        # 이전 버전 호환성
                        console.print(ui.file_added_panel(str(result)))
                else:
                    console.print(ui.error_panel("사용법: /add <file1|dir1> <file2|dir2> ...", "입력 오류"))
                continue

            elif user_input.lower() == '/files':
                console.print(ui.file_list_table(file_manager.files))
                continue

            elif user_input.lower() == '/tree':
                if file_manager.files:
                    console.print(ui.file_tree(file_manager.files))
                else:
                    console.print(ui.warning_panel("추가된 파일이 없습니다. '/add <파일경로>' 명령으로 파일을 추가하세요."))
                continue

            elif user_input.lower().startswith('/analyze '):
                parts = user_input.split()
                if len(parts) > 1:
                    directory_path = parts[1].replace('@', '')  # @ 제거
                    # 상대 경로를 절대 경로로 변환
                    if not os.path.isabs(directory_path):
                        directory_path = os.path.abspath(directory_path)
                    
                    if os.path.isdir(directory_path):
                        analysis = file_manager.analyze_directory_structure(directory_path)
                        console.print(ui.directory_analysis_panel(analysis))
                    else:
                        console.print(ui.error_panel(f"디렉토리를 찾을 수 없습니다: {directory_path}", "분석 오류"))
                else:
                    console.print(ui.error_panel("사용법: /analyze @<directory_path> 또는 /analyze <directory_path>", "입력 오류"))
                continue

            elif user_input.lower().startswith('/info '):
                parts = user_input.split()
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
                            analysis_result = ui.file_analysis_panel([{
                                'file_path': found_file_path,
                                'file_type': result['file_type'],
                                'analysis': result['analysis']
                            }])
                            if isinstance(analysis_result, list):
                                for panel in analysis_result:
                                    console.print(panel)
                                    console.print()
                            else:
                                console.print(analysis_result)
                        else:
                            console.print(ui.warning_panel(f"파일 분석 정보가 없습니다: {os.path.basename(found_file_path)}"))
                    else:
                        # 사용 가능한 파일들 표시
                        available_files = [os.path.basename(f) for f in file_manager.files.keys()]
                        console.print(ui.error_panel(
                            f"파일을 찾을 수 없습니다: {user_file_path}\n\n"
                            f"사용 가능한 파일들:\n" + 
                            "\n".join(f"• {f}" for f in available_files[:10]), 
                            "파일 오류"
                        ))
                else:
                    console.print(ui.error_panel("사용법: /info @<file_path>", "입력 오류"))
                continue

            elif user_input.lower() == '/clear':
                chat_history.clear()
                console.print(ui.success_panel("대화 기록이 초기화되었습니다.", "초기화 완료"))
                continue

            elif user_input.lower() == '/preview':
                if not last_edit_response:
                    console.print(ui.warning_panel("미리볼 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
                else:
                    preview = current_coder.preview_changes(last_edit_response, file_manager.files)
                    if 'error' in preview:
                        console.print(ui.error_panel(preview['error']['message'], f"미리보기 오류 ({preview['error']['strategy']})"))
                    else:
                        panels = ui.file_changes_preview(preview)
                        for panel in panels:
                            console.print(panel)
                continue

            elif user_input.lower() == '/apply':
                if not last_edit_response:
                    console.print(ui.warning_panel("적용할 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
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
                        console.print(ui.error_panel(f"파일 적용 중 오류 발생: {e}", "적용 실패"))
                continue

            elif user_input.lower() == '/history':
                operations = file_editor.get_history(10)
                console.print(ui.edit_history_table(operations))
                continue

            elif user_input.lower() == '/debug':
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
                    console.print(ui.warning_panel("디버그할 edit 응답이 없습니다."))
                continue


            elif user_input.lower().startswith('/rollback '):
                parts = user_input.split()
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
                        console.print(ui.error_panel(f"작업 ID '{operation_id}'를 찾을 수 없습니다.", "롤백 실패"))
                
                elif len(parts) == 3 and parts[1] != 'cancel':
                    operation_id, action = parts[1], parts[2]
                    if action == 'confirm':
                        try:
                            success = file_editor.rollback_operation(operation_id)
                            if success:
                                console.print(ui.rollback_success(operation_id))
                            else:
                                console.print(ui.error_panel(f"작업 '{operation_id}' 롤백에 실패했습니다.", "롤백 실패"))
                        except Exception as e:
                            console.print(ui.error_panel(f"롤백 중 오류 발생: {e}", "롤백 실패"))
                    else:
                        console.print(ui.error_panel("'/rollback <ID> confirm' 형식으로 입력하세요.", "명령어 오류"))
                
                elif len(parts) == 2 and parts[1] == 'cancel':
                    console.print(ui.success_panel("롤백이 취소되었습니다.", "취소됨"))
                
                else:
                    console.print(ui.error_panel("사용법: /rollback <ID> 또는 /rollback <ID> confirm", "명령어 오류"))
                continue

            elif user_input.lower() == '/ask':
                task = 'ask'
                ui.mode_switch_message(task)
                continue

            elif user_input.lower().startswith('/edit'):
                parts = user_input.split()
                if len(parts) == 1:
                    # 기본 edit 모드
                    task = 'edit'
                    ui.mode_switch_message(task)
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
                        console.print(ui.error_panel(f"알 수 없는 전략: {strategy_name}\\n사용 가능: {', '.join(available)}", "전략 오류"))
                else:
                    console.print(ui.error_panel("사용법: /edit 또는 /edit <전략명> (예: /edit udiff)", "명령어 오류"))
                continue

            elif user_input.strip() == "":
                continue

            # "수정해줘" 등 edit 요청 키워드 감지 시 edit 모드로 자동 전환
            elif any(keyword in user_input for keyword in ["수정해줘", "수정해 줘", "바꿔줘", "바꿔 줘", "고쳐줘", "고쳐 줘", "편집해줘", "편집해 줘"]):
                if task != 'edit':
                    task = 'edit'
                    console.print(f"[bold green]✅ '수정해줘' 요청으로 edit 모드로 자동 전환되었습니다.[/bold green]")
                    console.print(f"[dim]✏️ 이제 파일 수정을 요청할 수 있습니다.[/dim]\n")
                
                # edit 모드에서 처리하도록 계속 진행
                ui.separator()
                console.print(ui.user_question_panel(user_input))

            # 잘못된 명령어 처리 (/ 로 시작하지만 알려진 명령어가 아닌 경우)
            elif user_input.startswith('/'):
                known_commands = ['/add', '/files', '/tree', '/analyze', '/info', '/clear', '/preview', '/apply', 
                                '/history', '/debug', '/rollback', '/ask', '/edit', '/help', '/exit', '/quit']
                
                # 명령어 부분만 추출 (공백 전까지)
                command_part = user_input.split()[0].lower()
                
                if command_part not in known_commands:
                    console.print(ui.error_panel(
                        f"알 수 없는 명령어: '{command_part}'\n\n"
                        f"사용 가능한 명령어:\n"
                        f"• 파일 관리: /add, /files, /tree, /analyze, /info, /clear\n"
                        f"• 모드 전환: /ask, /edit\n"
                        f"• 편집 기능: /preview, /apply, /history, /rollback, /debug\n"
                        f"• 기타: /help, /exit\n\n"
                        f"'/help' 명령어로 자세한 도움말을 확인하세요.",
                        "명령어 오류"
                    ))
                    continue

            else:
                # 일반 사용자 입력 - AI에게 전달
                ui.separator()
                console.print(ui.user_question_panel(user_input))

            # Build the prompt using PromptBuilder
            prompt_builder = PromptBuilder(task)
            messages = prompt_builder.build(user_input, file_manager.files, chat_history, file_manager)

            # 로딩 메시지
            with ui.loading_spinner():
                llm_response = llm_service.chat_completion(messages)

            if llm_response and "choices" in llm_response:
                llm_message = llm_response["choices"][0]["message"]
                response_content = llm_message['content']
                
                # 모드에 따라 다른 응답 표시
                if task == 'edit':
                    # Edit 모드: 코드 생성 응답 표시
                    console.print(ui.edit_mode_response_panel(response_content))
                    
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
                            console.print(ui.info_columns({
                                "다음 단계": "'/preview' - 변경사항 다시 보기\n'/apply' - 변경사항 적용\n'/ask' - 질문 모드로 전환"
                            }))
                        elif preview and 'error' in preview:
                            console.print(ui.error_panel(preview['error']['message'], f"미리보기 오류 ({preview['error']['strategy']})"))
                    except Exception as e:
                        console.print(ui.warning_panel(f"미리보기 생성 중 오류: {e}"))
                else:
                    # Ask 모드: 일반 응답 표시
                    console.print(ui.ai_response_panel(response_content))

                # Add user input and LLM response to history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_content})
            else:
                console.print(ui.error_panel("AI가 응답을 생성하지 못했습니다."))
            
            console.print()  # 빈 줄 추가

        except KeyboardInterrupt:
            console.print(ui.warning_panel("작업이 중단되었습니다."))
            continue
        except EOFError:
            console.print(ui.goodbye_panel())
            break
        except ValueError as e:
            console.print(ui.error_panel(str(e), "입력 오류"))
            continue


if __name__ == '__main__':
    main()
