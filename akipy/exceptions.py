class InvalidLanguageError(ValueError):
    """Raise when the user input language is invalid or not supported by Akinator"""
    pass


class CantGoBackAnyFurther(Exception):
    """Raises when the user is in the first question and tries to go back further"""
    pass
