import click
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

@click.command()
def main():
    """An interactive REPL for the CoE LLM assistant."""
    # Use a file-based history to remember commands across sessions
    history = FileHistory('.coe-cli-history')
    session = PromptSession(history=history)

    click.echo("Welcome to the CoE CLI! Type /help for commands, or /exit to quit.")

    # This is the main REPL loop
    while True:
        try:
            user_input = session.prompt("> ")

            if user_input.lower() == '/exit':
                click.echo("Exiting CoE CLI.")
                break  # Exit the loop

            elif user_input.lower() == '/help':
                click.echo("Available commands:")
                click.echo("  /help - Show this help message")
                click.echo("  /exit - Exit the CLI")

            elif user_input.strip() == "":
                # If the user just presses Enter, do nothing and show a new prompt
                continue

            else:
                # Placeholder for future command processing
                click.echo(f"Command not yet implemented: {user_input}")

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully by starting a new line without exiting
            continue
        except EOFError:
            # Handle Ctrl+D to exit the application
            click.echo("Exiting CoE CLI.")
            break # Exit the loop

if __name__ == '__main__':
    main()