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
