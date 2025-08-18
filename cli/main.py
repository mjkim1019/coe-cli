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

@click.command()
def main():
    """An interactive REPL for the CoE LLM assistant."""
    history = FileHistory('.coe-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    llm_service = LLMService()
    chat_history = []
    task = 'ask'  # Default task

    click.echo("Welcome to the CoE CLI! Type /help for commands, or /exit to quit.")
    click.echo(f"Current task: {task}. Use /ask or /edit to switch.")

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.lower() in ('/exit', '/quit'):
                click.echo("Exiting CoE CLI.")
                break

            elif user_input.lower() == '/help':
                click.echo("Available commands:")
                click.echo("  /add <file1> <file2> ... - Add files to the session")
                click.echo("  /ask - Switch to 'ask' mode (for asking questions about code)")
                click.echo("  /edit - Switch to 'edit' mode (for requesting code changes)")
                click.echo("  /help - Show this help message")
                click.echo("  /exit or /quit - Exit the CLI")
                continue

            elif user_input.lower().startswith('/add '):
                parts = user_input.split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    message = file_manager.add(files_to_add)
                    click.echo(message)
                else:
                    click.echo("Usage: /add <file1> <file2> ...")
                continue

            elif user_input.lower() == '/ask':
                task = 'ask'
                click.echo(f"Switched to {task} mode.")
                continue

            elif user_input.lower() == '/edit':
                task = 'edit'
                click.echo(f"Switched to {task} mode.")
                continue

            elif user_input.strip() == "":
                continue

            # Build the prompt using PromptBuilder
            prompt_builder = PromptBuilder(task)
            messages = prompt_builder.build(user_input, file_manager.files, chat_history, file_manager)

            click.echo("Thinking...")
            llm_response = llm_service.chat_completion(messages)

            if llm_response and "choices" in llm_response:
                llm_message = llm_response["choices"][0]["message"]
                response_content = llm_message['content']
                click.echo(f"LLM: {response_content}")

                # Add user input and LLM response to history
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response_content})
            else:
                click.echo("LLM did not return a valid response.")

        except KeyboardInterrupt:
            continue
        except EOFError:
            click.echo("Exiting CoE CLI.")
            break
        except ValueError as e:
            click.echo(f"Error: {e}")
            continue


if __name__ == '__main__':
    main()
