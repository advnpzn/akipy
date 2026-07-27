"""
akipy - A Python wrapper library for Akinator

:copyright: (c) 2024, advnpzn
:license: MIT, see LICENSE for more details.
"""

from .akinator import Akinator as Akinator
from . import async_akinator as async_akinator
from .exceptions import (
    CantGoBackAnyFurther,
    CloudflareBlockedError,
    FlareSolverrError,
    InvalidChoiceError,
    InvalidLanguageError,
    SolverError,
)

__all__ = [
    "Akinator",
    "async_akinator",
    "CantGoBackAnyFurther",
    "CloudflareBlockedError",
    "FlareSolverrError",
    "InvalidChoiceError",
    "InvalidLanguageError",
    "SolverError",
]
