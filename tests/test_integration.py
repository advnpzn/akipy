"""
Integration tests that hit the real Akinator API.

These tests require internet connectivity and are excluded from the default
test run to keep CI fast. Run them explicitly with:

    pytest -m integration

or alongside the unit tests with:

    pytest -m "integration or not integration"
"""

import pytest
from akipy import Akinator
from akipy.async_akinator import Akinator as AsyncAkinator

pytestmark = [pytest.mark.integration, pytest.mark.slow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _play_to_win(aki: Akinator, max_steps: int = 40) -> None:
    """Answer 'yes' repeatedly until Akinator proposes a character."""
    for _ in range(max_steps):
        if aki.win:
            break
        aki.answer("yes")


async def _async_play_to_win(aki: AsyncAkinator, max_steps: int = 40) -> None:
    for _ in range(max_steps):
        if aki.win:
            break
        await aki.answer("yes")


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestSyncIntegration:
    def test_start_game_populates_session(self):
        """start_game must return a real question and fill all session fields."""
        with Akinator() as aki:
            aki.start_game("en")

            assert isinstance(aki.question, str) and len(aki.question) > 0
            assert aki.session is not None
            assert aki.signature is not None
            assert aki.identifiant is not None
            assert aki.step == "0"
            assert aki.progression == "0.00000"
            assert aki.uri == "https://en.akinator.com"
            assert aki.lang == "en"
            assert aki.finished is False
            assert aki.win is False

    def test_answer_advances_step(self):
        """Answering a question must move to the next step (or trigger a win)."""
        with Akinator() as aki:
            aki.start_game("en")
            aki.answer("yes")
            assert aki.win or int(aki.step) > 0

    def test_all_answer_types_accepted(self):
        """All five answer strings and their integer equivalents must be accepted."""
        answers = ["yes", "no", "i dont know", "probably", "probably not"]
        with Akinator() as aki:
            aki.start_game("en")
            for ans in answers:
                if aki.win or aki.finished:
                    break
                aki.answer(ans)

        # Integer equivalents
        with Akinator() as aki:
            aki.start_game("en")
            for ans in range(5):
                if aki.win or aki.finished:
                    break
                aki.answer(ans)

    def test_back_returns_to_previous_question(self):
        """Going back from step 2 must restore the step-1 question."""
        with Akinator() as aki:
            aki.start_game("en")
            aki.answer("yes")  # step 0 → 1
            if aki.win:
                pytest.skip("Won too early to test back()")
            question_at_1 = aki.question
            aki.answer("yes")  # step 1 → 2
            if aki.win:
                pytest.skip("Won too early to test back()")
            aki.back()  # step 2 → 1
            assert aki.question == question_at_1
            assert int(aki.step) == 1

    def test_confidence_is_valid_float(self):
        """confidence property must stay in [0, 1] throughout the game."""
        with Akinator() as aki:
            aki.start_game("en")
            assert aki.confidence == 0.0
            aki.answer("yes")
            assert 0.0 <= aki.confidence <= 1.0

    def test_akitude_url_is_well_formed(self):
        """akitude_url must be a full URL pointing to a .png on the Akinator CDN."""
        with Akinator() as aki:
            aki.start_game("en")
            url = aki.akitude_url
            assert url.startswith(
                "https://en.akinator.com/assets/img/akitudes_670x1096/"
            )
            assert url.endswith(".png")

    def test_full_game_reaches_win(self):
        """Answering 'yes' to every question must eventually produce a win proposition."""
        with Akinator() as aki:
            aki.start_game("en")
            _play_to_win(aki)

            assert aki.win is True, (
                "Akinator should propose a character within 40 answers"
            )
            assert (
                isinstance(aki.name_proposition, str) and len(aki.name_proposition) > 0
            )
            assert isinstance(aki.description_proposition, str)
            assert aki.photo is not None

    def test_choose_finishes_game(self):
        """Accepting the win proposition must mark the game as finished."""
        with Akinator() as aki:
            aki.start_game("en")
            _play_to_win(aki)

            if not aki.win or aki.finished:
                pytest.skip("Could not reach a non-finished win state")

            aki.choose()
            assert aki.finished is True
            assert aki.win is True
            assert aki.akitude == "triomphe.png"
            assert float(aki.progression) == 100.0

    def test_exclude_continues_game(self):
        """Rejecting the win proposition must reset win state and continue the game."""
        with Akinator() as aki:
            aki.start_game("en")
            _play_to_win(aki)

            if not aki.win or aki.finished:
                pytest.skip("Could not reach a non-finished win state")

            aki.exclude()
            assert aki.win is False

    def test_str_returns_question_during_game(self):
        """str(aki) must return the current question while the game is in progress."""
        with Akinator() as aki:
            aki.start_game("en")
            assert str(aki) == aki.question

    def test_str_returns_proposition_on_win(self):
        """str(aki) must include the character name when Akinator has won."""
        with Akinator() as aki:
            aki.start_game("en")
            _play_to_win(aki)

            if not aki.win or aki.finished:
                pytest.skip("Could not reach a non-finished win state")

            result = str(aki)
            assert aki.name_proposition in result

    def test_french_language(self):
        """Starting with language='fr' must connect to the French Akinator server."""
        with Akinator() as aki:
            aki.start_game("fr")
            assert aki.lang == "fr"
            assert aki.uri == "https://fr.akinator.com"
            assert isinstance(aki.question, str) and len(aki.question) > 0

    def test_full_language_name(self):
        """Passing a full language name like 'french' must resolve to the correct code."""
        with Akinator() as aki:
            aki.start_game("french")
            assert aki.lang == "fr"
            assert isinstance(aki.question, str) and len(aki.question) > 0

    def test_child_mode(self):
        """Child mode must start without error and return a valid question."""
        with Akinator() as aki:
            aki.start_game("en", child_mode=True)
            assert aki.child_mode is True
            assert isinstance(aki.question, str) and len(aki.question) > 0


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAsyncIntegration:
    @pytest.mark.asyncio
    async def test_start_game_populates_session(self):
        """async start_game must return a real question and fill all session fields."""
        async with AsyncAkinator() as aki:
            await aki.start_game("en")

            assert isinstance(aki.question, str) and len(aki.question) > 0
            assert aki.session is not None
            assert aki.signature is not None
            assert aki.identifiant is not None
            assert aki.step == "0"
            assert aki.progression == "0.00000"
            assert aki.uri == "https://en.akinator.com"
            assert aki.lang == "en"
            assert aki.finished is False
            assert aki.win is False

    @pytest.mark.asyncio
    async def test_answer_advances_step(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await aki.answer("yes")
            assert aki.win or int(aki.step) > 0

    @pytest.mark.asyncio
    async def test_all_answer_types_accepted(self):
        answers = ["yes", "no", "i dont know", "probably", "probably not"]
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            for ans in answers:
                if aki.win or aki.finished:
                    break
                await aki.answer(ans)

    @pytest.mark.asyncio
    async def test_back_returns_to_previous_question(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await aki.answer("yes")
            if aki.win:
                pytest.skip("Won too early to test back()")
            question_at_1 = aki.question
            await aki.answer("yes")
            if aki.win:
                pytest.skip("Won too early to test back()")
            await aki.back()
            assert aki.question == question_at_1
            assert int(aki.step) == 1

    @pytest.mark.asyncio
    async def test_confidence_is_valid_float(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            assert aki.confidence == 0.0
            await aki.answer("yes")
            assert 0.0 <= aki.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_full_game_reaches_win(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await _async_play_to_win(aki)

            assert aki.win is True, (
                "Akinator should propose a character within 40 answers"
            )
            assert (
                isinstance(aki.name_proposition, str) and len(aki.name_proposition) > 0
            )
            assert isinstance(aki.description_proposition, str)
            assert aki.photo is not None

    @pytest.mark.asyncio
    async def test_choose_finishes_game(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await _async_play_to_win(aki)

            if not aki.win or aki.finished:
                pytest.skip("Could not reach a non-finished win state")

            await aki.choose()
            assert aki.finished is True
            assert aki.win is True
            assert aki.akitude == "triomphe.png"
            assert float(aki.progression) == 100.0

    @pytest.mark.asyncio
    async def test_exclude_continues_game(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await _async_play_to_win(aki)

            if not aki.win or aki.finished:
                pytest.skip("Could not reach a non-finished win state")

            await aki.exclude()
            assert aki.win is False

    @pytest.mark.asyncio
    async def test_french_language(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("fr")
            assert aki.lang == "fr"
            assert aki.uri == "https://fr.akinator.com"
            assert isinstance(aki.question, str) and len(aki.question) > 0

    @pytest.mark.asyncio
    async def test_child_mode(self):
        async with AsyncAkinator() as aki:
            await aki.start_game("en", child_mode=True)
            assert aki.child_mode is True
            assert isinstance(aki.question, str) and len(aki.question) > 0

    @pytest.mark.asyncio
    async def test_yes_no_convenience_methods(self):
        """yes() and no() must work identically to answer('yes') / answer('no')."""
        async with AsyncAkinator() as aki:
            await aki.start_game("en")
            await aki.yes()
            if not aki.win:
                await aki.no()
