"""Regression coverage for the current /game page contract."""

import httpx
import pytest

from akipy import Akinator
from akipy.async_akinator import Akinator as AsyncAkinator
from akipy.exceptions import CantGoBackAnyFurther


CURRENT_GAME_HTML = """
<div class="bubble-body"><p class="question-text"
 id="question-label">Is your character real?</p></div>
<div class="sub-bubble-propose"><p id="p-sub-bubble">I think of</p></div>
<script>
localStorage.setItem('step', '1');
localStorage.setItem('progression', '0');
localStorage.setItem('session', 'current_session');
localStorage.setItem('identifiant', 'current_identifiant');
$('#session').val('current_session');
$('#identifiant').val('current_identifiant');
</script>
"""


def test_sync_current_page_start_and_answer(mocker):
    request = mocker.patch(
        "akipy.akinator.request_handler",
        side_effect=[
            httpx.Response(
                200,
                text=CURRENT_GAME_HTML,
                request=httpx.Request("POST", "https://en.akinator.com/game"),
            ),
            httpx.Response(
                200,
                json={
                    "completion": "OK",
                    "step": 2,
                    "progression": 12.5,
                    "question": "Is your character human?",
                },
                request=httpx.Request("POST", "https://en.akinator.com/answer"),
            ),
            httpx.Response(
                200,
                json={
                    "step": 3,
                    "progression": 0,
                    "question": "Is your character real?",
                },
                request=httpx.Request("POST", "https://en.akinator.com/cancel_answer"),
            ),
        ],
    )
    aki = Akinator(solver_url="")
    try:
        aki.start_game()
        assert (aki.session, aki.identifiant, aki.signature) == (
            "current_session",
            "current_identifiant",
            None,
        )
        assert (aki.step, aki.progression, aki.question) == (
            "1",
            "0",
            "Is your character real?",
        )
        with pytest.raises(CantGoBackAnyFurther):
            aki.back()
        aki.answer("yes")
        assert aki.completion == "OK"
        assert aki.step == 2
        data = request.call_args.kwargs["data"]
        assert data["step"] == "1"
        assert data["session"] == "current_session"
        assert "signature" not in data
        aki.back()
        assert aki.question == "Is your character real?"
        with pytest.raises(CantGoBackAnyFurther):
            aki.back()
    finally:
        aki.client.close()


@pytest.mark.asyncio
async def test_async_current_page_start_and_answer(mocker):
    request = mocker.patch(
        "akipy.async_akinator.async_request_handler",
        side_effect=[
            httpx.Response(
                200,
                text=CURRENT_GAME_HTML,
                request=httpx.Request("POST", "https://en.akinator.com/game"),
            ),
            httpx.Response(
                200,
                json={
                    "completion": "OK",
                    "step": 2,
                    "progression": 12.5,
                    "question": "Is your character human?",
                },
                request=httpx.Request("POST", "https://en.akinator.com/answer"),
            ),
            httpx.Response(
                200,
                json={
                    "step": 3,
                    "progression": 0,
                    "question": "Is your character real?",
                },
                request=httpx.Request("POST", "https://en.akinator.com/cancel_answer"),
            ),
        ],
    )
    async with AsyncAkinator(solver_url="") as aki:
        await aki.start_game()
        assert (aki.step, aki.progression, aki.signature) == ("1", "0", None)
        with pytest.raises(CantGoBackAnyFurther):
            await aki.back()
        await aki.answer("yes")
        assert aki.completion == "OK"
        assert aki.step == 2
        data = request.call_args.kwargs["data"]
        assert data["step"] == "1"
        assert data["session"] == "current_session"
        assert "signature" not in data
        await aki.back()
        assert aki.question == "Is your character real?"
        with pytest.raises(CantGoBackAnyFurther):
            await aki.back()
