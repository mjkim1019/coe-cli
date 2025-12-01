# AGENTS.md

Project: {{ project_name }}
Created at {{ created_at }}
- Use `ls` or `tree` to navigate your project directory and quickly locate packages or modules.
- Run `pip install -e .` from the package root to install your package in editable mode, allowing local changes to take effect immediately.
- Use `python -m venv venv` followed by `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows) to create and activate a virtual environment for your project.
- Check the `setup.py` or `pyproject.toml` files for the correct package name and entry points.

## Testing Instructions
- Find the CI pipeline configuration in the `.github/workflows` directory.
- Run `pytest` from the package root to execute all tests for that package.
- To run a specific test, use: `pytest path/to/test_file.py -k "<test_function_name>"`.
- Fix any failing tests or type errors until the entire test suite passes.
- After moving files or changing imports, run `flake8` or `pylint` to check for linting and type errors.
- Add or update tests for any code you change, even if it's not specifically requested.

## PR Instructions
- Title format: [`<package_name>`] <Title>
- Always run `flake8` and `pytest` before committing to ensure code quality and test coverage.
