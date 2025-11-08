# Examples

This directory contains example scripts demonstrating different ways to use the akipy library.

## Files

### Basic Usage

- **`basic_usage.py`** - Simple synchronous usage without context manager
  - Shows basic game flow
  - Manual resource management

### Async Usage

- **`async_usage.py`** - Simple asynchronous usage without context manager
  - Demonstrates async/await syntax
  - Manual resource management

### Context Manager Usage (Recommended)

- **`context_manager_usage.py`** - Synchronous usage with context manager
  - **Recommended approach** for production code
  - Automatic resource cleanup
  - Prevents memory leaks
  - Better connection pooling

- **`async_context_manager.py`** - Asynchronous usage with async context manager
  - **Recommended approach** for async production code
  - Automatic async resource cleanup
  - Proper async client lifecycle management

## Running Examples

Make sure you have akipy installed first:

```bash
# Install the package
pip install akipy

# Or in development mode
cd /path/to/akipy
uv sync
```

Then run any example:

```bash
# Basic synchronous example
python examples/basic_usage.py

# Async example
python examples/async_usage.py

# Context manager example (recommended)
python examples/context_manager_usage.py

# Async context manager example (recommended for async)
python examples/async_context_manager.py
```

## Best Practices

### Use Context Managers

Always prefer context managers in production code:

```python
# Good - automatic cleanup
with akipy.Akinator() as aki:
    aki.start_game()
    # ... your code ...

# Avoid - manual cleanup required
aki = akipy.Akinator()
aki.start_game()
# ... your code ...
aki.close()  # Easy to forget!
```

### For Async Code

```python
# Good - automatic cleanup
async with Akinator() as aki:
    await aki.start_game()
    # ... your code ...

# Avoid - manual cleanup required
aki = Akinator()
await aki.start_game()
# ... your code ...
await aki.close()  # Easy to forget!
```

### Error Handling

Always handle exceptions properly:

```python
try:
    aki.answer("yes")
except akipy.InvalidChoiceError:
    print("Invalid choice!")
except akipy.CantGoBackAnyFurther:
    print("Can't go back further!")
```

## Answer Options

You can answer questions with:

- `"yes"`, `"y"`, or `0`
- `"no"`, `"n"`, or `1`
- `"idk"`, `"i don't know"`, or `2`
- `"probably"`, `"p"`, or `3`
- `"probably not"`, `"pn"`, or `4`
- `"b"` to go back (custom in examples)

## Language Support

You can start the game in different languages:

```python
aki.start_game(language="fr")  # French
aki.start_game(language="es")  # Spanish
aki.start_game(language="de")  # German
# ... and many more!
```

## Child Mode

Enable child mode for family-friendly content:

```python
aki.start_game(child_mode=True)
```
