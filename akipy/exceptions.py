class InvalidLanguageError(ValueError):
    """Raise when the user input language is invalid or not supported by Akinator"""

    pass


class CantGoBackAnyFurther(Exception):
    """Raise when the user is in the first question and tries to go back further"""

    pass


class InvalidChoiceError(ValueError):
    """Raise when the user input is not a valid answer for the current question"""

    pass

class InvalidThemeError(ValueError):
    """Raise when the user input theme is not a valid theme for the selected language"""

    pass

class CloudflareBlockedError(Exception):
    """Raise when Cloudflare blocks the request and no challenge solver is configured."""

    def __init__(
        self,
        message: str = (
            "Request blocked by Cloudflare. Pass solver_url to Akinator() "
            "to solve the challenge via FlareSolverr, TRAWL, or any "
            "FlareSolverr-compatible service "
            "(e.g. solver_url='http://localhost:8191')."
        ),
    ):
        super().__init__(message)

class SolverError(Exception):
    """Raise when a challenge solver (FlareSolverr, TRAWL, etc.) fails or returns non-ok."""

    pass

FlareSolverrError = SolverError  # alias

