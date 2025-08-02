"""
akipy - A Python wrapper library for Akinator

:copyright: (c) 2024, advnpzn
:license: MIT, see LICENSE for more details.
"""

from .akinator import Akinator as Akinator
from . import async_akipy as async_akipy
from .exceptions import (
    InvalidLanguageError,
    CantGoBackAnyFurther,
    InvalidChoiceError,
)

__all__ = [
    "Akinator",
    "async_akipy",
    "InvalidLanguageError",
    "CantGoBackAnyFurther",
    "InvalidChoiceError",
]
