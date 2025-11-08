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
- [Contributing](#contributing)

## Features

- Both synchronous and asynchronous API support
- Context manager support for automatic resource cleanup
- Type hints for better IDE support
- Comprehensive error handling with custom exceptions
- Multiple language support
- Child mode support

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

# Contributing

For contributing to this library, please check [CONTRIBUTING.md](CONTRIBUTING.md)
