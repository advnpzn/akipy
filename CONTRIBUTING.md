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
# Run unit tests (integration tests are excluded by default)
uv run pytest

# Check code quality
uv run ruff check .

# Run type checking
uv run mypy akipy
```

### 5. Integration tests (optional, live API)

Integration tests hit the real Akinator API and need a FlareSolverr-compatible solver for Cloudflare ([FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) or [TRAWL](https://github.com/germondai/trawl)). Do not commit the URL; pass it with an env var:

```bash
export AKIPY_SOLVER_URL="http://localhost:8191"   # FlareSolverr, TRAWL, or remote
# legacy alias:
# export AKIPY_FLARESOLVERR_URL="http://localhost:8191"

# Full suite (local development)
uv run pytest -m integration

# Same smoke subset CI runs (~10 tests)
uv run pytest -m "integration and integration_core"
```

**How CI is detected:** we do **not** branch inside tests on `if CI`. GitHub Actions sets `CI=true` and `GITHUB_ACTIONS=true` automatically, and the workflow command selects the smoke marker:

```bash
pytest -m "integration and integration_core"
```

Locally `CI` is unset; use `-m integration` for the full suite (including full games, choose/exclude, etc.).

**GitHub Actions:** the `integration-test` job starts a solver service on the runner (`http://127.0.0.1:8191`) and runs the `integration_core` subset only.

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
