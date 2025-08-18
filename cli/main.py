import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager
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
    llm_service = LLMService()
    chat_history = []
    task = 'ask'  # Default task

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
                
                # AI 응답 표시
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
