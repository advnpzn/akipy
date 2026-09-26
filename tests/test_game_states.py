"""Current Akinator response and terminal-state behavior."""

import httpx
import pytest

from akipy import Akinator, AkinatorServerError
from akipy.async_akinator import Akinator as AsyncAkinator


def api_response(data=None, *, text=None, path="answer"):
    return httpx.Response(
        200,
        json=data if text is None else None,
        text=text,
        request=httpx.Request("POST", f"https://en.akinator.com/{path}"),
    )


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_guess_uses_response_step_and_tracks_terminal_fields(akinator_type):
    aki = akinator_type()
    aki.step = 11
    aki.handle_response(
        api_response(
            {
                "completion": "OK",
                "id_proposition": 42,
                "step": 13,
                "no_question": "1",
                "valide_contrainte": 1,
                "name_proposition": "A character",
            }
        )
    )
    assert aki.win is True
    assert aki.no_question is True
    assert aki.step_last_proposition == "13"


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_child_mode_restriction_ends_game_without_proposing(akinator_type):
    aki = akinator_type()
    aki.handle_response(
        api_response(
            {
                "completion": "OK",
                "id_proposition": 42,
                "step": 13,
                "valide_contrainte": 0,
            }
        )
    )
    assert aki.child_mode_blocked is True
    assert aki.finished is True
    assert aki.win is False
    assert aki.id_proposition == ""
    assert aki.name_proposition == ""


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_ko_raises_without_changing_game_state(akinator_type):
    aki = akinator_type()
    aki.question = "Current question?"
    aki.step = 3
    with pytest.raises(AkinatorServerError, match="rejected"):
        aki.handle_response(api_response({"completion": "KO"}))
    assert aki.question == "Current question?"
    assert aki.step == 3
    assert aki.completion == "OK"


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_soundlike_is_distinct_from_defeat(akinator_type):
    aki = akinator_type()
    aki.handle_response(api_response({"completion": "SOUNDLIKE"}))
    assert aki.soundlike is True
    assert aki.finished is True
    assert aki.win is False
    assert aki.akitude != "deception.png"


def test_sync_exhausted_guess_transitions_to_soundlike(mocker):
    request = mocker.patch(
        "akipy.akinator.request_handler",
        return_value=api_response({"step": 15}, path="exclude"),
    )
    aki = Akinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.no_question = True
    aki.step = 13
    aki.exclude()
    assert request.call_args.kwargs["data"]["forward_answer"] == "0"
    assert aki.step == 15
    assert (aki.finished, aki.win, aki.soundlike) == (True, False, True)


def test_answer_after_rejected_guess_sends_guess_step(mocker):
    request = mocker.patch(
        "akipy.akinator.request_handler",
        side_effect=[
            api_response({"completion": "OK", "id_proposition": 42, "step": 13}),
            api_response(
                {"step": 15, "progression": 50, "question": "Next?"}, path="exclude"
            ),
            api_response({"completion": "OK", "step": 16, "question": "After?"}),
        ],
    )
    aki = Akinator()
    aki.uri = "https://en.akinator.com"
    aki.step = 11
    aki.answer(0)
    aki.exclude()
    aki.answer(0)
    assert request.call_args.kwargs["data"]["step_last_proposition"] == "13"


@pytest.mark.asyncio
async def test_async_exhausted_guess_transitions_to_soundlike(mocker):
    request = mocker.patch(
        "akipy.async_akinator.async_request_handler",
        return_value=api_response({"step": 15}, path="exclude"),
    )
    aki = AsyncAkinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.no_question = True
    aki.step = 13
    await aki.exclude()
    assert request.call_args.kwargs["data"]["forward_answer"] == "0"
    assert aki.step == 15
    assert (aki.finished, aki.win, aki.soundlike) == (True, False, True)


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_rejected_terminal_transition_preserves_guess(akinator_type):
    aki = akinator_type()
    aki.win = True
    aki.no_question = True
    aki.step = 13
    with pytest.raises(AkinatorServerError, match="rejected"):
        aki.handle_soundlike_transition(
            api_response({"completion": "KO"}, path="exclude")
        )
    assert aki.win is True
    assert aki.finished is False
    assert aki.step == 13


@pytest.mark.asyncio
async def test_async_answer_after_rejected_guess_sends_guess_step(mocker):
    request = mocker.patch(
        "akipy.async_akinator.async_request_handler",
        side_effect=[
            api_response({"completion": "OK", "id_proposition": 42, "step": 13}),
            api_response(
                {"step": 15, "progression": 50, "question": "Next?"}, path="exclude"
            ),
            api_response({"completion": "OK", "step": 16, "question": "After?"}),
        ],
    )
    aki = AsyncAkinator()
    aki.uri = "https://en.akinator.com"
    aki.step = 11
    await aki.answer(0)
    await aki.exclude()
    await aki.answer(0)
    assert request.call_args.kwargs["data"]["step_last_proposition"] == "13"


@pytest.mark.parametrize("akinator_type", [Akinator, AsyncAkinator])
def test_question_response_clears_prior_proposal(akinator_type):
    aki = akinator_type()
    aki.win = True
    aki.no_question = True
    aki.id_proposition = "42"
    aki.handle_response(api_response({"step": 15, "question": "Next?"}, path="exclude"))
    assert aki.win is False
    assert aki.no_question is False
    assert aki.id_proposition == ""


def test_exclude_can_return_another_guess(mocker):
    mocker.patch(
        "akipy.akinator.request_handler",
        return_value=api_response(
            {"id_proposition": 43, "step": 15, "name_proposition": "Another"},
            path="exclude",
        ),
    )
    aki = Akinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.id_proposition = "42"
    aki.exclude()
    assert aki.win is True
    assert aki.id_proposition == 43
    assert aki.step_last_proposition == "15"


@pytest.mark.asyncio
async def test_async_exclude_can_return_another_guess(mocker):
    mocker.patch(
        "akipy.async_akinator.async_request_handler",
        return_value=api_response(
            {"id_proposition": 43, "step": 15, "name_proposition": "Another"},
            path="exclude",
        ),
    )
    aki = AsyncAkinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.id_proposition = "42"
    await aki.exclude()
    assert aki.win is True
    assert aki.id_proposition == 43
    assert aki.step_last_proposition == "15"


def test_sync_exclude_error_preserves_guess(mocker):
    mocker.patch(
        "akipy.akinator.request_handler",
        return_value=api_response(
            text="<html>A technical problem has occurred.</html>", path="exclude"
        ),
    )
    aki = Akinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.id_proposition = "42"
    with pytest.raises(RuntimeError, match="technical problem"):
        aki.exclude()
    assert aki.win is True
    assert aki.finished is False
    assert aki.id_proposition == "42"


@pytest.mark.asyncio
async def test_async_exclude_error_preserves_guess(mocker):
    mocker.patch(
        "akipy.async_akinator.async_request_handler",
        return_value=api_response(
            text="<html>A technical problem has occurred.</html>", path="exclude"
        ),
    )
    aki = AsyncAkinator()
    aki.uri = "https://en.akinator.com"
    aki.win = True
    aki.id_proposition = "42"
    with pytest.raises(RuntimeError, match="technical problem"):
        await aki.exclude()
    assert aki.win is True
    assert aki.finished is False
    assert aki.id_proposition == "42"
