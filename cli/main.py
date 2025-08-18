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
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.rule import Rule

@click.command()
def main():
    """An interactive REPL for the CoE LLM assistant."""
    console = Console()
    history = FileHistory('.coe-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    llm_service = LLMService()
    chat_history = []
    task = 'ask'  # Default task

    # 웰컴 메시지
    console.print(Panel.fit(
        Text("🚀 CoE CLI - LLM Assistant", style="bold cyan", justify="center"),
        style="bright_blue",
        title="환영합니다!",
        subtitle="Type /help for commands, or /exit to quit"
    ))
    console.print(f"[bold green]Current task:[/bold green] [yellow]{task}[/yellow] (Use /ask or /edit to switch)\n")

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.lower() in ('/exit', '/quit'):
                console.print(Panel(
                    "[bold red]👋 안녕히 가세요![/bold red]",
                    style="red",
                    title="종료",
                    expand=False
                ))
                break

            elif user_input.lower() == '/help':
                help_text = """
[bold cyan]📋 사용 가능한 명령어:[/bold cyan]

[yellow]/add[/yellow] <file1> <file2> ... - 파일을 세션에 추가
[yellow]/ask[/yellow] - 코드에 대해 질문하는 'ask' 모드로 전환
[yellow]/edit[/yellow] - 코드 수정을 요청하는 'edit' 모드로 전환
[yellow]/help[/yellow] - 이 도움말 메시지 표시
[yellow]/exit[/yellow] or [yellow]/quit[/yellow] - CLI 종료

[dim]💡 팁: .c 파일과 .sql 파일은 자동으로 구조를 분석합니다![/dim]
                """
                console.print(Panel(help_text, title="📖 도움말", style="bright_blue"))
                continue

            elif user_input.lower().startswith('/add '):
                parts = user_input.split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    message = file_manager.add(files_to_add)
                    console.print(Panel(
                        f"[green]{message}[/green]",
                        title="📁 파일 추가 완료",
                        style="bright_green"
                    ))
                else:
                    console.print("[red]❌ 사용법: /add <file1> <file2> ...[/red]")
                continue

            elif user_input.lower() == '/ask':
                task = 'ask'
                console.print(f"[bold green]✅ '{task}' 모드로 전환되었습니다.[/bold green]")
                console.print(f"[dim]💬 이제 코드에 대해 질문할 수 있습니다.[/dim]\n")
                continue

            elif user_input.lower() == '/edit':
                task = 'edit'
                console.print(f"[bold green]✅ '{task}' 모드로 전환되었습니다.[/bold green]")
                console.print(f"[dim]✏️  이제 코드 수정을 요청할 수 있습니다.[/dim]\n")
                continue

            elif user_input.strip() == "":
                continue

            # 사용자 입력 표시
            console.print(Rule(style="dim"))
            console.print(Panel(
                user_input,
                title="🤔 Your Question",
                title_align="left",
                style="bright_cyan",
                border_style="cyan"
            ))

            # Build the prompt using PromptBuilder
            prompt_builder = PromptBuilder(task)
            messages = prompt_builder.build(user_input, file_manager.files, chat_history, file_manager)

            # 로딩 메시지
            with console.status("[bold green]🧠 AI가 생각중입니다...", spinner="dots"):
                llm_response = llm_service.chat_completion(messages)

            if llm_response and "choices" in llm_response:
                llm_message = llm_response["choices"][0]["message"]
                response_content = llm_message['content']
                
                # AI 응답 표시
                console.print(Panel(
                    Markdown(response_content),
                    title="🤖 AI Response",
                    title_align="left",
                    style="bright_green",
                    border_style="green"
                ))

                # Add user input and LLM response to history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_content})
            else:
                console.print(Panel(
                    "[red]❌ AI가 응답을 생성하지 못했습니다.[/red]",
                    title="오류",
                    style="red"
                ))
            
            console.print()  # 빈 줄 추가

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  작업이 중단되었습니다.[/yellow]")
            continue
        except EOFError:
            console.print(Panel(
                "[bold red]👋 안녕히 가세요![/bold red]",
                style="red",
                title="종료",
                expand=False
            ))
            break
        except ValueError as e:
            console.print(Panel(
                f"[red]❌ 오류: {e}[/red]",
                title="입력 오류",
                style="red"
            ))
            continue


if __name__ == '__main__':
    main()
