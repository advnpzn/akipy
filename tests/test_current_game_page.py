"""Regression coverage for the current /game page contract."""

import httpx
import pytest

from akipy import Akinator
from akipy.async_akinator import Akinator as AsyncAkinator
from akipy.exceptions import CantGoBackAnyFurther


CURRENT_GAME_HTML = """
<img id="akitude" src="/assets/img/akitudes_670x1096/serein_2.png" alt="akitude"/>
<div class="bubble-body"><p class="question-text"
 id="question-label">Is your character real?</p></div>
<div class="sub-bubble-propose"><p id="p-sub-bubble">I think of</p></div>
<script>
localStorage.setItem('step', '1');
localStorage.setItem('progression', '0');
localStorage.setItem('trouvitudesReponses', '[20, 0, 0, 0, 0]');
localStorage.setItem('session', 'current_session');
localStorage.setItem('identifiant', 'current_identifiant');
$('#session').val('current_session');
$('#identifiant').val('current_identifiant');
</script>
"""


def game_json(data):
    return httpx.Response(
        200,
        json=data,
        request=httpx.Request("POST", "https://en.akinator.com/answer"),
    )


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
                    "trouvitudesReponses": [0, 0, 0, 0, 0],
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
        assert aki.akinator_image_url == (
            "https://en.akinator.com/assets/img/akitudes_670x1096/serein_2.png"
        )
        with pytest.raises(CantGoBackAnyFurther):
            aki.back()
        aki.answer("yes")
        assert aki.completion == "OK"
        assert aki.step == 2
        assert aki.akitude == "serein_1.png"
        data = request.call_args.kwargs["data"]
        assert data["step"] == "1"
        assert data["session"] == "current_session"
        assert "signature" not in data
        aki.back()
        assert aki.question == "Is your character real?"
        assert aki.akitude == "serein_2.png"
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
                    "trouvitudesReponses": [0, 0, 0, 0, 0],
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
        assert aki.akinator_image_url == aki.akitude_url
        with pytest.raises(CantGoBackAnyFurther):
            await aki.back()
        await aki.answer("yes")
        assert aki.completion == "OK"
        assert aki.step == 2
        assert aki.akitude == "serein_1.png"
        data = request.call_args.kwargs["data"]
        assert data["step"] == "1"
        assert data["session"] == "current_session"
        assert "signature" not in data
        await aki.back()
        assert aki.question == "Is your character real?"
        assert aki.akitude == "serein_2.png"
        with pytest.raises(CantGoBackAnyFurther):
            await aki.back()


def test_png_mood_uses_selected_answer_score_and_restores_on_back(mocker):
    request = mocker.patch(
        "akipy.akinator.request_handler",
        side_effect=[
            httpx.Response(200, text=CURRENT_GAME_HTML),
            game_json(
                {
                    "completion": "OK",
                    "step": 2,
                    "progression": 0,
                    "question": "Second question?",
                    "trouvitudesReponses": [0, 0, 0, 0, 0],
                },
            ),
            game_json(
                {
                    "completion": "OK",
                    "step": 3,
                    "progression": 0,
                    "question": "Third question?",
                    "trouvitudesReponses": [0, 0, 0, 0, 0],
                },
            ),
            game_json(
                {
                    "completion": "OK",
                    "step": 2,
                    "progression": 0,
                    "question": "Second question?",
                    "trouvitudesReponses": [0, 0, 0, 0, 0],
                },
            ),
        ],
    )
    with Akinator(solver_url="") as aki:
        aki.start_game()
        aki.answer("yes")
        assert aki.akitude == "serein_1.png"
        aki.answer("no")
        assert aki.akitude == "concentration.png"
        aki.back()
        assert aki.akitude == "serein_1.png"
        assert aki.akinator_image_url.endswith("/serein_1.png")
    assert request.call_count == 4


def test_png_mood_proposal_uses_current_state():
    aki = Akinator(solver_url="")
    try:
        aki._parse_init_response(CURRENT_GAME_HTML)
        aki.step = "10"
        aki.handle_response(
            game_json({"completion": "OK", "step": 11, "question": "Next?"}),
            answer_index=1,
        )
        assert aki.akitude == "surprise.png"
        aki.handle_response(
            game_json({"completion": "OK", "step": 11, "id_proposition": "123"})
        )
        assert aki.akitude == "espoir_anxieux.png"
    finally:
        if aki.client is not None:
            aki.client.close()
