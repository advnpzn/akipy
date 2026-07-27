# akipy

[![PyPI version](https://img.shields.io/pypi/v/akipy?color=blue)](https://pypi.org/project/akipy/)
[![Downloads](https://img.shields.io/pypi/dm/akipy?color=orange)](https://pypi.org/project/akipy/)
[![Python Version](https://img.shields.io/pypi/pyversions/akipy)](https://pypi.org/project/akipy/)
[![License](https://img.shields.io/github/license/advnpzn/akipy)](LICENSE)
[![Repo Size](https://img.shields.io/github/repo-size/advnpzn/akipy?color=yellow)](https://github.com/advnpzn/akipy)

A Python wrapper library for the Akinator game API. Akinator is the popular web-based game that guesses characters you're thinking of by asking a series of questions. This library allows you to integrate Akinator's functionality into your Python applications with both synchronous and asynchronous support.

## Table of Contents

- [Features](#features)
- [Quick Links](#quick-links)
- [Installation](#installation)
- [Usage](#usage)
- [Cloudflare / challenge solvers](#cloudflare--challenge-solvers-optional)
- [Contributing](#contributing)

## Features

- Both synchronous and asynchronous API support
- Context manager support for automatic resource cleanup
- Type hints for better IDE support
- Comprehensive error handling with custom exceptions
- Multiple language support
- Child mode support
- Optional Cloudflare bypass via [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr), [TRAWL](https://github.com/germondai/trawl), or any FlareSolverr v2-compatible solver

## Quick Links

- [PyPI Package](https://pypi.org/project/akipy/)
- [GitHub Repository](https://github.com/advnpzn/akipy)
- [Issues](https://github.com/advnpzn/akipy/issues)
- [Examples](examples/)

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

## Cloudflare / challenge solvers (optional)

If Akinator is behind Cloudflare, pass a solver that speaks the [FlareSolverr v2](https://github.com/FlareSolverr/FlareSolverr) `POST /v1` API:

| Solver | Notes |
|--------|--------|
| [FlareSolverr](https://github.com/FlareSolverr/FlareSolverr) | Cloudflare proxy |
| [TRAWL](https://github.com/germondai/trawl) | FlareSolverr-compatible API |
| Other v2-compatible proxies | Same request format |

Direct requests run first. On a Cloudflare challenge, akipy calls the solver once, applies cookies and User-Agent to the client, then continues over normal HTTP.

### Run a solver locally

FlareSolverr:

```bash
docker run -d --name=flaresolverr -p 8191:8191 ghcr.io/flaresolverr/flaresolverr:latest
```

TRAWL:

```bash
docker run -d --name=trawl -p 8191:8191 --shm-size=1gb ghcr.io/germondai/trawl:latest
```

### Use with akipy

```python
import akipy

# FlareSolverr, TRAWL, or any compatible host
aki = akipy.Akinator(solver_url="http://localhost:8191")
# aki = akipy.Akinator(solver_url="https://trawl.example.com")
# aki = akipy.Akinator(solver_url="localhost:8191")  # defaults to http
# aki = akipy.Akinator(solver_url="https://fs.example.com/v1")

aki.start_game()
```

Or set the env var:

```bash
export AKIPY_SOLVER_URL="http://localhost:8191"
```

`AKIPY_FLARESOLVERR_URL` and `flaresolverr_url=` still work as aliases.

### Errors

| Exception | When |
|-----------|------|
| `CloudflareBlockedError` | Challenge detected and no `solver_url` configured |
| `SolverError` | Solver unreachable or returned a non-ok status (`FlareSolverrError` is an alias) |

# Contributing

For contributing to this library, please check [CONTRIBUTING.md](CONTRIBUTING.md)
