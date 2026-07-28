"""Tests for custom exceptions"""

import pytest
from akipy.exceptions import (
    InvalidLanguageError,
    CantGoBackAnyFurther,
    CloudflareBlockedError,
    FlareSolverrError,
    InvalidChoiceError,
    SolverError,
    InvalidThemeError,
)


class TestInvalidLanguageError:
    """Tests for InvalidLanguageError exception"""

    def test_invalid_language_error_inherits_from_value_error(self):
        """Test that InvalidLanguageError inherits from ValueError"""
        assert issubclass(InvalidLanguageError, ValueError)

    def test_invalid_language_error_can_be_raised(self):
        """Test that InvalidLanguageError can be raised"""
        with pytest.raises(InvalidLanguageError):
            raise InvalidLanguageError("invalid_lang")

    def test_invalid_language_error_message(self):
        """Test that InvalidLanguageError carries the message"""
        with pytest.raises(InvalidLanguageError, match="invalid_lang"):
            raise InvalidLanguageError("invalid_lang")


class TestCantGoBackAnyFurther:
    """Tests for CantGoBackAnyFurther exception"""

    def test_cant_go_back_any_further_inherits_from_exception(self):
        """Test that CantGoBackAnyFurther inherits from Exception"""
        assert issubclass(CantGoBackAnyFurther, Exception)

    def test_cant_go_back_any_further_can_be_raised(self):
        """Test that CantGoBackAnyFurther can be raised"""
        with pytest.raises(CantGoBackAnyFurther):
            raise CantGoBackAnyFurther("At first question")

    def test_cant_go_back_any_further_message(self):
        """Test that CantGoBackAnyFurther carries the message"""
        with pytest.raises(CantGoBackAnyFurther, match="first question"):
            raise CantGoBackAnyFurther("You are at the first question")


class TestInvalidChoiceError:
    """Tests for InvalidChoiceError exception"""

    def test_invalid_choice_error_inherits_from_value_error(self):
        """Test that InvalidChoiceError inherits from ValueError"""
        assert issubclass(InvalidChoiceError, ValueError)

    def test_invalid_choice_error_can_be_raised(self):
        """Test that InvalidChoiceError can be raised"""
        with pytest.raises(InvalidChoiceError):
            raise InvalidChoiceError("Invalid choice")

    def test_invalid_choice_error_message(self):
        """Test that InvalidChoiceError carries the message"""
        with pytest.raises(InvalidChoiceError, match="Invalid"):
            raise InvalidChoiceError("Invalid choice made")


class TestInvalidThemeError:
    """Tests for InvalidChoiceError exception"""

    def test_invalid_theme_error_inherits_from_value_error(self):
        """Test that InvalidChoiceError inherits from ValueError"""
        assert issubclass(InvalidThemeError, ValueError)

    def test_invalid_theme_error_can_be_raised(self):
        """Test that InvalidChoiceError can be raised"""
        with pytest.raises(InvalidThemeError):
            raise InvalidThemeError("Invalid theme for language")

    def test_invalid_theme_error_message(self):
        """Test that InvalidChoiceError carries the message"""
        with pytest.raises(InvalidThemeError, match="Invalid"):
            raise InvalidThemeError("Invalid theme chosen for language")


class TestCloudflareBlockedError:
    def test_inherits_from_exception(self):
        assert issubclass(CloudflareBlockedError, Exception)

    def test_default_message_mentions_solver(self):
        with pytest.raises(CloudflareBlockedError, match="solver_url"):
            raise CloudflareBlockedError()


class TestSolverError:
    def test_inherits_from_exception(self):
        assert issubclass(SolverError, Exception)

    def test_can_be_raised_with_message(self):
        with pytest.raises(SolverError, match="timeout"):
            raise SolverError("timeout")

    def test_flaresolverr_error_is_alias(self):
        assert FlareSolverrError is SolverError
