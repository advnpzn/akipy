"""
Integration tests that hit the real Akinator API.

These tests need internet and a FlareSolverr-compatible solver
(FlareSolverr, TRAWL, etc.) when Cloudflare blocks direct access.

Local (full suite)::

    export AKIPY_SOLVER_URL=http://localhost:8191
    pytest -m integration

CI (smoke subset only). GitHub Actions sets ``CI=true`` and
``GITHUB_ACTIONS=true`` automatically. The workflow runs::

    pytest -m "integration and integration_core"

Tests marked ``integration_core`` (~10) cover start/answer/back/lang/async
smoke without multi-step full games.
"""

from __future__ import annotations

import os

import httpx
import pytest

from akipy import Akinator
from akipy.async_akinator import Akinator as AsyncAkinator
from akipy.solver import apply_solver_solution, normalize_solver_url, solve_challenge

pytestmark = [pytest.mark.integration, pytest.mark.slow]

# Marker for the CI smoke subset (see module docstring).
core = pytest.mark.integration_core

# Longer than library default so cold FlareSolverr CF solves can finish on CI.
_SOLVER_TIMEOUT_MS = 180_000


# ---------------------------------------------------------------------------
# Fixtures: Akinator with challenge solver from env/secret
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def solver_url() -> str:
    """Require AKIPY_SOLVER_URL or AKIPY_FLARESOLVERR_URL for integration tests."""
    url = (
        os.environ.get("AKIPY_SOLVER_URL", "").strip()
        or os.environ.get("AKIPY_FLARESOLVERR_URL", "").strip()
    )
    if not url:
        pytest.skip(
            "AKIPY_SOLVER_URL (or AKIPY_FLARESOLVERR_URL) is not set. "
            "Integration tests need a FlareSolverr-compatible solver "
            "(FlareSolverr, TRAWL, etc.). Set the env var or GitHub secret."
        )
    normalized = normalize_solver_url(url)
    if not normalized:
        pytest.skip(f"Invalid solver URL: {url!r}")
    return normalized


@pytest.fixture(scope="module")
def cf_clearance(solver_url: str) -> dict:
    """
    Warm Cloudflare clearance once per module via GET on the site origin.

    Avoids every test opening a new FlareSolverr browser solve (often times out
    when runs are stacked on CI).
    """
    return solve_challenge(
        solver_url=solver_url,
        url="https://en.akinator.com/",
        method="GET",
        data=None,
        max_timeout=_SOLVER_TIMEOUT_MS,
    )


def _apply_clearance(client: httpx.Client | httpx.AsyncClient, clearance: dict) -> None:
    apply_solver_solution(client, clearance)


@pytest.fixture
def aki(solver_url: str, cf_clearance: dict):
    """Sync Akinator with solver + pre-warmed CF cookies."""
    with Akinator(solver_url=solver_url, solver_timeout=_SOLVER_TIMEOUT_MS) as instance:
        instance.client = httpx.Client(timeout=30.0)
        _apply_clearance(instance.client, cf_clearance)
        yield instance


@pytest.fixture
async def async_aki(solver_url: str, cf_clearance: dict):
    """Async Akinator with solver + pre-warmed CF cookies."""
    async with AsyncAkinator(
        solver_url=solver_url, solver_timeout=_SOLVER_TIMEOUT_MS
    ) as instance:
        instance.client = httpx.AsyncClient(timeout=30.0)
        _apply_clearance(instance.client, cf_clearance)
        yield instance


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
    @core
    def test_start_game_populates_session(self, aki: Akinator):
        """start_game must return a real question and fill all session fields."""
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
        assert aki.solver_url is not None

    @core
    def test_answer_advances_step(self, aki: Akinator):
        """Answering a question must move to the next step (or trigger a win)."""
        aki.start_game("en")
        aki.answer("yes")
        assert aki.win or int(aki.step) > 0

    def test_all_answer_types_accepted(self, solver_url: str):
        """All five answer strings and their integer equivalents must be accepted."""
        answers = ["yes", "no", "i dont know", "probably", "probably not"]
        with Akinator(solver_url=solver_url) as aki:
            aki.start_game("en")
            for ans in answers:
                if aki.win or aki.finished:
                    break
                aki.answer(ans)

        # Integer equivalents
        with Akinator(solver_url=solver_url) as aki:
            aki.start_game("en")
            for ans in range(5):
                if aki.win or aki.finished:
                    break
                aki.answer(ans)

    @core
    def test_back_returns_to_previous_question(self, aki: Akinator):
        """Going back from step 2 must restore the step-1 question."""
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

    @core
    def test_confidence_is_valid_float(self, aki: Akinator):
        """confidence property must stay in [0, 1] throughout the game."""
        aki.start_game("en")
        assert aki.confidence == 0.0
        aki.answer("yes")
        assert 0.0 <= aki.confidence <= 1.0

    def test_akitude_url_is_well_formed(self, aki: Akinator):
        """akitude_url must be a full URL pointing to a .png on the Akinator CDN."""
        aki.start_game("en")
        url = aki.akitude_url
        assert url.startswith("https://en.akinator.com/assets/img/akitudes_670x1096/")
        assert url.endswith(".png")

    def test_full_game_reaches_win(self, aki: Akinator):
        """Answering 'yes' to every question must eventually produce a win proposition."""
        aki.start_game("en")
        _play_to_win(aki)

        assert aki.win is True, "Akinator should propose a character within 40 answers"
        assert isinstance(aki.name_proposition, str) and len(aki.name_proposition) > 0
        assert isinstance(aki.description_proposition, str)
        assert aki.photo is not None

    def test_choose_finishes_game(self, aki: Akinator):
        """Accepting the win proposition must mark the game as finished."""
        aki.start_game("en")
        _play_to_win(aki)

        if not aki.win or aki.finished:
            pytest.skip("Could not reach a non-finished win state")

        aki.choose()
        assert aki.finished is True
        assert aki.win is True
        assert aki.akitude == "triomphe.png"
        assert float(aki.progression) == 100.0

    def test_exclude_continues_game(self, aki: Akinator):
        """Rejecting the win proposition must reset win state and continue the game."""
        aki.start_game("en")
        _play_to_win(aki)

        if not aki.win or aki.finished:
            pytest.skip("Could not reach a non-finished win state")

        aki.exclude()
        assert aki.win is False

    def test_str_returns_question_during_game(self, aki: Akinator):
        """str(aki) must return the current question while the game is in progress."""
        aki.start_game("en")
        assert str(aki) == aki.question

    def test_str_returns_proposition_on_win(self, aki: Akinator):
        """str(aki) must include the character name when Akinator has won."""
        aki.start_game("en")
        _play_to_win(aki)

        if not aki.win or aki.finished:
            pytest.skip("Could not reach a non-finished win state")

        result = str(aki)
        assert aki.name_proposition in result

    @core
    def test_french_language(self, aki: Akinator):
        """Starting with language='fr' must connect to the French Akinator server."""
        aki.start_game("fr")
        assert aki.lang == "fr"
        assert aki.uri == "https://fr.akinator.com"
        assert isinstance(aki.question, str) and len(aki.question) > 0

    def test_full_language_name(self, aki: Akinator):
        """Passing a full language name like 'french' must resolve to the correct code."""
        aki.start_game("french")
        assert aki.lang == "fr"
        assert isinstance(aki.question, str) and len(aki.question) > 0

    @core
    def test_child_mode(self, aki: Akinator):
        """Child mode must start without error and return a valid question."""
        aki.start_game("en", child_mode=True)
        assert aki.child_mode is True
        assert isinstance(aki.question, str) and len(aki.question) > 0

    @core
    def test_game_mode(self, aki: Akinator):
        """Different game modes must result in the proper index for the specified language"""
        aki.start_game("en", game_mode="c")
        assert aki.theme == 1
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0

    def test_game_mode_animal(self, aki: Akinator):
        """Different game modes must result in the proper index for the specified language"""
        aki.start_game("en", game_mode="a")
        assert aki.theme == 14
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0

    def test_game_mode_object(self, aki: Akinator):
        """Different game modes must result in the proper index for the specified language"""
        aki.start_game("en", game_mode="a")
        assert aki.theme == 2
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestAsyncIntegration:
    @core
    @pytest.mark.asyncio
    async def test_start_game_populates_session(self, async_aki: AsyncAkinator):
        """async start_game must return a real question and fill all session fields."""
        await async_aki.start_game("en")

        assert isinstance(async_aki.question, str) and len(async_aki.question) > 0
        assert async_aki.session is not None
        assert async_aki.signature is not None
        assert async_aki.identifiant is not None
        assert async_aki.step == "0"
        assert async_aki.progression == "0.00000"
        assert async_aki.uri == "https://en.akinator.com"
        assert async_aki.lang == "en"
        assert async_aki.finished is False
        assert async_aki.win is False
        assert async_aki.solver_url is not None

    @core
    @pytest.mark.asyncio
    async def test_answer_advances_step(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        await async_aki.answer("yes")
        assert async_aki.win or int(async_aki.step) > 0

    @pytest.mark.asyncio
    async def test_all_answer_types_accepted(self, solver_url: str):
        answers = ["yes", "no", "i dont know", "probably", "probably not"]
        async with AsyncAkinator(solver_url=solver_url) as aki:
            await aki.start_game("en")
            for ans in answers:
                if aki.win or aki.finished:
                    break
                await aki.answer(ans)

    @core
    @pytest.mark.asyncio
    async def test_back_returns_to_previous_question(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        await async_aki.answer("yes")
        if async_aki.win:
            pytest.skip("Won too early to test back()")
        question_at_1 = async_aki.question
        await async_aki.answer("yes")
        if async_aki.win:
            pytest.skip("Won too early to test back()")
        await async_aki.back()
        assert async_aki.question == question_at_1
        assert int(async_aki.step) == 1

    @pytest.mark.asyncio
    async def test_confidence_is_valid_float(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        assert async_aki.confidence == 0.0
        await async_aki.answer("yes")
        assert 0.0 <= async_aki.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_full_game_reaches_win(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        await _async_play_to_win(async_aki)

        assert async_aki.win is True, (
            "Akinator should propose a character within 40 answers"
        )
        assert (
            isinstance(async_aki.name_proposition, str)
            and len(async_aki.name_proposition) > 0
        )
        assert isinstance(async_aki.description_proposition, str)
        assert async_aki.photo is not None

    @pytest.mark.asyncio
    async def test_choose_finishes_game(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        await _async_play_to_win(async_aki)

        if not async_aki.win or async_aki.finished:
            pytest.skip("Could not reach a non-finished win state")

        await async_aki.choose()
        assert async_aki.finished is True
        assert async_aki.win is True
        assert async_aki.akitude == "triomphe.png"
        assert float(async_aki.progression) == 100.0

    @pytest.mark.asyncio
    async def test_exclude_continues_game(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en")
        await _async_play_to_win(async_aki)

        if not async_aki.win or async_aki.finished:
            pytest.skip("Could not reach a non-finished win state")

        await async_aki.exclude()
        assert async_aki.win is False

    @pytest.mark.asyncio
    async def test_french_language(self, async_aki: AsyncAkinator):
        await async_aki.start_game("fr")
        assert async_aki.lang == "fr"
        assert async_aki.uri == "https://fr.akinator.com"
        assert isinstance(async_aki.question, str) and len(async_aki.question) > 0

    @pytest.mark.asyncio
    async def test_child_mode(self, async_aki: AsyncAkinator):
        await async_aki.start_game("en", child_mode=True)
        assert async_aki.child_mode is True
        assert isinstance(async_aki.question, str) and len(async_aki.question) > 0

    @pytest.mark.asyncio
    async def test_game_mode(self, aki: Akinator):
        await aki.start_game("en", game_mode="c")
        assert aki.theme == 1
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0

    @pytest.mark.asyncio
    async def test_game_mode_animal(self, aki: Akinator):
        await aki.start_game("en", game_mode="a")
        assert aki.theme == 14
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0

    @pytest.mark.asyncio
    async def test_game_mode_object(self, aki: Akinator):
        await aki.start_game("en", game_mode="a")
        assert aki.theme == 2
        assert isinstance(aki.theme, int)
        assert isinstance(aki.question, str) and len(aki.question) > 0

    @core
    @pytest.mark.asyncio
    async def test_yes_no_convenience_methods(self, async_aki: AsyncAkinator):
        """yes() and no() must work identically to answer('yes') / answer('no')."""
        await async_aki.start_game("en")
        await async_aki.yes()
        if not async_aki.win:
            await async_aki.no()
