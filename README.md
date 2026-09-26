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
- [Game state and images](#game-state-and-images)
- [Async usage](#async-usage)
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

This example covers questions, guesses, Back, and a finished game. A context
manager closes the HTTP client when you leave it.

```python
import akipy

with akipy.Akinator() as aki:
    aki.start_game(language="en", game_mode="c", child_mode=False)

    while not aki.finished:
        if aki.win:
            print(f"My guess: {aki.name_proposition} ({aki.description_proposition})")
            print(f"Character photo: {aki.photo}")
            if input("Is that right? [y/n] ").strip().lower() == "y":
                aki.choose()
            else:
                aki.exclude()
            continue

        print(f"Question {aki.step}: {aki.question}")
        print(f"Akinator image: {aki.akinator_image_url}")
        reply = input("yes/no/idk/probably/probably not/back: ").strip().lower()
        if reply == "back":
            try:
                aki.back()
            except akipy.CantGoBackAnyFurther:
                print("Already at the first question.")
        else:
            try:
                aki.answer(reply)
            except akipy.InvalidChoiceError:
                print("Please enter one of the listed answers.")

    if aki.child_mode_blocked:
        print("Akinator's guess was hidden by child mode.")
    elif aki.soundlike:
        print("Akinator ran out of questions and guesses.")
    elif aki.win:
        print(f"Akinator guessed {aki.name_proposition}.")
    else:
        print("Game ended without a correct guess.")
```

The five answer choices are `yes`, `no`, `idk`, `probably`, and `probably not`.
You can also pass their numeric IDs, `0` through `4`. `back` is handled by the
example; it is not an answer you pass to `aki.answer()`.

Use `game_mode="c"` for characters, `"a"` for animals, or `"o"` for objects.
Availability depends on the language.

## Game state and images

After `start_game()` and after each action, read these fields from the same
`Akinator` instance:

| Field | What it tells you |
|-------|-------------------|
| `question` | Current question text. |
| `step` | Current server step. |
| `progression` / `confidence` | Progress as a server value / a float from 0 to 1. |
| `akinator_image_url` | URL of the current PNG fallback image. `akitude_url` is an alias. |
| `win` | Akinator has proposed a character, or you accepted its guess. |
| `name_proposition`, `description_proposition`, `photo` | Details of the proposed character. Read these when `win` is true. |
| `no_question` | There are no more questions after the current guess. Rejecting it ends the game. |
| `child_mode_blocked` | A proposed character was hidden by child mode. |
| `soundlike` | The game reached its sounds-like ending. |
| `finished` | The game is over. Check `win`, `child_mode_blocked`, and `soundlike` for the outcome. |
| `completion` | Last server result, usually `"OK"`. Rejected requests raise an exception. |

The image URL changes as you answer and returns to the previous image when
you call `back()`. It points to the site's PNG fallback, not a frame from its
animated Lottie artwork. If an API response omits the scores used to select
the next image, the last known PNG stays available.

A guess does not finish the game on its own. Call `choose()` to accept it or
`exclude()` to reject it. If `no_question` is true, `exclude()` ends the game.
The `yes()` and `no()` helpers also work: on a question they answer yes or no;
on a guess they accept or reject it.

## Async usage

The async client exposes the same state fields and uses `await` for game
actions:

```python
import asyncio
from akipy.async_akinator import Akinator

async def play():
    async with Akinator() as aki:
        await aki.start_game(language="en")
        while not aki.finished:
            if aki.win:
                print(f"Akinator guesses {aki.name_proposition}: {aki.photo}")
                if input("Correct? [y/n] ").strip().lower() == "y":
                    await aki.choose()
                else:
                    await aki.exclude()
            else:
                print(aki.question, aki.akinator_image_url)
                await aki.answer(input("Your answer: ").strip().lower())

asyncio.run(play())
```

An expired or out-of-sync session raises `AkinatorServerError` when Akinator
returns `completion="KO"`. A session timeout raises `TimeoutError`. Start a
new game in either case. See [Errors](#errors) for Cloudflare and solver errors.

## Cloudflare / challenge solvers (optional)

Most games work without a solver. akipy sends a browser-style User-Agent on
normal HTTP requests. If Cloudflare challenges those requests, you can pass a
solver that speaks the [FlareSolverr v2](https://github.com/FlareSolverr/FlareSolverr) `POST /v1` API:

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

CI integration tests start **FlareSolverr** as a service on the runner (`http://127.0.0.1:8191`). Remote public solvers are often unreachable from GitHub Actions (403 from edge WAF).

### Errors

| Exception | When |
|-----------|------|
| `CloudflareBlockedError` | Challenge detected and no `solver_url` configured |
| `SolverError` | Solver unreachable or returned a non-ok status (`FlareSolverrError` is an alias) |
| `AkinatorServerError` | Akinator rejected the game request, often because the session expired or the game state is out of sync |

# Contributing

For contributing to this library, please check [CONTRIBUTING.md](CONTRIBUTING.md)
