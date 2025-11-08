# akipy
Python library wrapper for [akinator.com](https://akinator.com)
You can use this in your python projects to integrate Akinator functionalities.

Wrapper is still in development.
Some things may or may not work. If you experience issues, feel free to raise an issue here.

Some things that could be improved:
* Exception Handling
* Docs
* Better error Handling
* Custom Exceptions

If you want to help, the above is the main priority for now.

# Why ?
I already used to use a wrapper library for Akinator ([akinator.py](https://github.com/Ombucha/akinator.py)) before.
But suddenly it seems to be not working. I debugged and made
sure the problem is because of API changes from Akinator themselves.
There were so many changes making me think I would have to change a lot of things.
So instead of doing that, I just made it from scratch. Obviously I took a lot
of inspiration from the old Python wrapper I was using thus the code structure
would look very similar. In fact, I'm trying to replicate the same interface that
was present in the old wrapper. Because I don't want to make changes to any piece
of software that may depend on this library (which isn't working now).

I hope there isn't any interface breaking changes here. If there are any, please
contact me either through Telegram or raise an issue here on GitHub or if you want
to help, raise a Pull Request.

# Installation

`pip install akipy`

# Usage

There is both synchronous and asynchronous variants of `akipy` available.

Synchronous: `from akipy import Akinator`

Asynchronous: `from akipy.async_akinator import Akinator`

I'll provide a sample usage for synchronous usage of `Akinator`.
All the examples are also in the project's examples folder. So please check them out as well.

```python
import akipy

aki = akipy.Akinator()
aki.start_game()

while not aki.win:
    ans = input(str(aki) + "\n\t")
    if ans == "b":
        try:
            aki.back()
        except akipy.CantGoBackAnyFurther:
            pass
    else:
        try:
            aki.answer(ans)
        except akipy.InvalidChoiceError:
            pass

print(aki)
print(aki.name_proposition)
print(aki.description_proposition)
print(aki.pseudo)
print(aki.photo)
```

# Developer Setup

## First Time Setup

If you're a developer who just cloned this repository, follow these steps to set up your development environment:

### 1. Install uv (if not already installed)
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Install dependencies
```bash
# Install all dependencies including dev dependencies
uv sync
```

This will:
- Create a virtual environment
- Install all production dependencies from `pyproject.toml`
- Install all development dependencies (pytest, ruff, mypy, pre-commit, etc.)

### 3. Install pre-commit hooks
```bash
# Install git hooks for automatic code quality checks
uv run pre-commit install
uv run pre-commit install --hook-type pre-push
```

### 4. Verify setup
```bash
# Run tests to ensure everything is working
uv run pytest

# Check code quality
uv run ruff check .

# Run type checking
uv run mypy akipy
```

## Development Workflow

### Making Changes

When you're working on changes to the codebase, follow these steps:

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Edit the code as needed
   - Add/update tests in the `tests/` directory
   - Ensure your code follows the project's style

3. **Test your changes**
   ```bash
   # Run all tests
   uv run pytest

   # Run tests with coverage
   uv run pytest --cov=akipy --cov-report=html

   # Run specific test file
   uv run pytest tests/test_akinator.py
   ```

4. **Check code quality** (optional - pre-commit will do this automatically)
   ```bash
   # Run linter
   uv run ruff check .

   # Auto-fix linting issues
   uv run ruff check --fix .

   # Format code
   uv run ruff format .

   # Type checking
   uv run mypy akipy
   ```

### Committing Changes

When you commit changes, pre-commit hooks will automatically run:

```bash
git add .
git commit -m "Your commit message"
```

The pre-commit hooks will automatically:
- Remove trailing whitespace
- Fix end-of-file issues
- Validate YAML/TOML files
- Check for debug statements
- Run ruff linter (with auto-fix)
- Format code with ruff

If any hook fails and can't auto-fix:
- Fix the issues reported
- Stage the fixed files with `git add`
- Try committing again

### Pushing Changes

When you push to GitHub, additional checks run:

```bash
git push origin feature/your-feature-name
```

The pre-push hook will:
- Run the entire test suite
- Only allow push if all tests pass

If tests fail:
- Review the test failures
- Fix the issues
- Re-run `uv run pytest` to verify
- Push again


## Project Structure

```
akipy/
├── akipy/                  # Main package source code
│   ├── __init__.py
│   ├── akinator.py         # Synchronous Akinator class
│   ├── async_akinator.py   # Asynchronous Akinator class
│   ├── dicts.py            # Constants and mappings
│   ├── exceptions.py       # Custom exceptions
│   └── utils.py            # Utility functions
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_akinator.py
│   ├── test_async_akipy.py
│   ├── test_utils.py
│   ├── test_exceptions.py
│   └── test_dicts.py
├── examples/               # Example usage scripts
├── .github/workflows/      # CI/CD configuration
├── pyproject.toml          # Project metadata and dependencies
└── README.md               # This file
```
