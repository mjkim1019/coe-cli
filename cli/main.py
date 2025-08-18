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
from cli.ui.components import SwingUIComponents

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
    last_edit_response = None  # 마지막 edit 응답 저장

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
                    message = file_manager.add(files_to_add)
                    console.print(ui.file_added_panel(message))
                else:
                    console.print(ui.error_panel("사용법: /add <file1> <file2> ...", "입력 오류"))
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

            elif user_input.lower() == '/clear':
                chat_history.clear()
                console.print(ui.success_panel("대화 기록이 초기화되었습니다.", "초기화 완료"))
                continue

            elif user_input.lower() == '/preview':
                if not last_edit_response:
                    console.print(ui.warning_panel("미리볼 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
                else:
                    preview = file_editor.preview_changes(last_edit_response)
                    panels = ui.file_changes_preview(preview)
                    for panel in panels:
                        console.print(panel)
                continue

            elif user_input.lower() == '/apply':
                if not last_edit_response:
                    console.print(ui.warning_panel("적용할 edit 응답이 없습니다. edit 모드에서 먼저 요청하세요."))
                else:
                    try:
                        operation = file_editor.apply_changes(last_edit_response, "사용자 요청으로 적용")
                        console.print(ui.apply_confirmation(len(operation.changes)))
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
                        f"[bold]마지막 Edit 응답 원문:[/bold]\n\n{last_edit_response[:1000]}{'...' if len(last_edit_response) > 1000 else ''}",
                        title="🐛 디버그 정보",
                        style="yellow"
                    ))
                    
                    # 파싱 테스트
                    parsed = file_editor.parse_edit_response(last_edit_response)
                    console.print(Panel(
                        f"[bold]파싱 결과:[/bold]\n" + 
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

            elif user_input.lower() == '/edit':
                task = 'edit'
                ui.mode_switch_message(task)
                continue

            elif user_input.strip() == "":
                continue

            # 사용자 입력 표시
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
                    
                    # 마지막 edit 응답 저장
                    last_edit_response = response_content
                    
                    # 자동으로 미리보기 표시
                    try:
                        preview = file_editor.preview_changes(response_content)
                        if preview:
                            console.print()
                            panels = ui.file_changes_preview(preview)
                            for panel in panels:
                                console.print(panel)
                            
                            console.print()
                            console.print(ui.info_columns({
                                "다음 단계": "'/preview' - 변경사항 다시 보기\n'/apply' - 변경사항 적용\n'/ask' - 질문 모드로 전환"
                            }))
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
