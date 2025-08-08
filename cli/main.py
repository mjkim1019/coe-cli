import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager
from cli.completer import PathCompleter
from llm.service import LLMService

@click.command()
def main():
    """An interactive REPL for the CoE LLM assistant."""
    history = FileHistory('.coe-cli-history')
    session = PromptSession(history=history, completer=PathCompleter())
    file_manager = FileManager()
    llm_service = LLMService()

    click.echo("Welcome to the CoE CLI! Type /help for commands, or /exit to quit.")

    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.lower() == '/exit':
                click.echo("Exiting CoE CLI.")
                break

            elif user_input.lower() == '/help':
                click.echo("Available commands:")
                click.echo("  /add <file1> <file2> ... - Add files to the session")
                click.echo("  /help - Show this help message")
                click.echo("  /exit - Exit the CLI")

            elif user_input.lower().startswith('/add '):
                parts = user_input.split()
                if len(parts) > 1:
                    files_to_add = [p.replace('@', '') for p in parts[1:]]
                    message = file_manager.add(files_to_add)
                    click.echo(message)
                else:
                    click.echo("Usage: /add <file1> <file2> ...")

            elif user_input.strip() == "":
                continue

            else:
                # Prepare messages for LLM
                messages = []
                # Add file contents as system messages
                for file_path, content in file_manager.files.items():
                    messages.append({"role": "system", "content": f"File: {file_path}\n```\n{content}\n```"})
                # Add user's prompt
                messages.append({"role": "user", "content": user_input})

                click.echo("Thinking...")
                llm_response = llm_service.chat_completion(messages)

                if llm_response and "choices" in llm_response:
                    # Assuming the response structure is similar to OpenAI API
                    llm_message = llm_response["choices"][0]["message"]
                    click.echo(f"LLM: {llm_message['content']}")
                else:
                    click.echo("LLM did not return a valid response.")

        except KeyboardInterrupt:
            continue
        except EOFError:
            click.echo("Exiting CoE CLI.")
            break

if __name__ == '__main__':
    main()
