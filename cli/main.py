import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from actions.file_manager import FileManager

@click.command()
def main():
    """An interactive REPL for the CoE LLM assistant."""
    history = FileHistory('.coe-cli-history')
    session = PromptSession(history=history)
    file_manager = FileManager()

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
                    message = file_manager.add(parts[1:])
                    click.echo(message)
                else:
                    click.echo("Usage: /add <file1> <file2> ...")

            elif user_input.strip() == "":
                continue

            else:
                click.echo(f"Command not yet implemented: {user_input}")

        except KeyboardInterrupt:
            continue
        except EOFError:
            click.echo("Exiting CoE CLI.")
            break

if __name__ == '__main__':
    main()