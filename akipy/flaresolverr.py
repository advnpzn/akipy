"""Compatibility re-exports. Import from :mod:`akipy.solver` instead."""

from .solver import (  # noqa: F401
    DEFAULT_FLARESOLVERR_TIMEOUT_MS,
    DEFAULT_SOLVER_TIMEOUT_MS,
    apply_flaresolverr_solution,
    apply_solver_solution,
    async_solve_challenge,
    async_solve_with_flaresolverr,
    is_cloudflare_challenge,
    normalize_flaresolverr_url,
    normalize_solver_url,
    raise_if_cloudflare_blocked,
    response_from_solution,
    solve_challenge,
    solve_with_flaresolverr,
)

__all__ = [
    "DEFAULT_FLARESOLVERR_TIMEOUT_MS",
    "DEFAULT_SOLVER_TIMEOUT_MS",
    "apply_flaresolverr_solution",
    "apply_solver_solution",
    "async_solve_challenge",
    "async_solve_with_flaresolverr",
    "is_cloudflare_challenge",
    "normalize_flaresolverr_url",
    "normalize_solver_url",
    "raise_if_cloudflare_blocked",
    "response_from_solution",
    "solve_challenge",
    "solve_with_flaresolverr",
]
