"""Pytest configuration and fixtures"""

import pytest
from unittest.mock import Mock
import httpx


@pytest.fixture
def mock_httpx_response():
    """Create a mock httpx Response object"""

    def _create_response(status_code=200, text="", json_data=None, headers=None):
        response = Mock(spec=httpx.Response)
        response.status_code = status_code
        response.text = text
        response.json.return_value = json_data if json_data else {}
        response.headers = headers or {}
        response.raise_for_status = Mock()
        return response

    return _create_response


@pytest.fixture
def mock_game_initialization_response():
    """Mock response for game initialization"""
    return (
        "<html><head></head><body><script>"
        "$('#session').val('test_session_123');"
        "$('#signature').val('test_signature_456');"
        "$('#identifiant').val('test_identifiant_789');"
        "</script>"
        '<div class="bubble-body">'
        '<p class="question-text" id="question-label">Is your character real?</p>'
        "</div>"
        '<div class="sub-bubble-propose">'
        '<p id="p-sub-bubble">I think of</p>'
        "</div>"
        "</body></html>"
    )


@pytest.fixture
def mock_answer_response_json():
    """Mock JSON response for answering questions"""
    return {
        "completion": "OK",
        "akitude": "concentre.png",
        "step": "1",
        "progression": "10.5",
        "question": "Is your character from a movie?",
    }


@pytest.fixture
def mock_win_response_json():
    """Mock JSON response for a win"""
    return {
        "completion": "OK",
        "id_proposition": "12345",
        "name_proposition": "Mario",
        "description_proposition": "Italian plumber from Nintendo",
        "pseudo": "Mario Bros",
        "flag_photo": "https://example.com/flag.jpg",
        "photo": "https://example.com/mario.jpg",
    }


@pytest.fixture
def mock_choice_response():
    """Mock response for choosing a character"""
    return """
    <html>
        <span class="win-sentence">Well done!</span>
        let tokenDejaJoue = "Already played";
        let timesSelected = "42";
        <span id="timesselected"></span> times
    </html>
    """


@pytest.fixture
def akinator_instance():
    """Create a basic Akinator instance"""
    from akipy import Akinator

    return Akinator()


@pytest.fixture
def initialized_akinator(akinator_instance, mocker):
    """Create an initialized Akinator instance with mocked session data"""
    aki = akinator_instance
    aki.uri = "https://en.akinator.com"
    aki.theme = 1
    aki.session = "test_session"
    aki.signature = "test_signature"
    aki.identifiant = "test_identifiant"
    aki.lang = "en"
    aki.child_mode = False
    aki.question = "Is your character real?"
    aki.progression = "0.00000"
    aki.step = "0"
    aki.akitude = "defi.png"
    aki.proposition_message = "I think of"
    aki.completion = "OK"
    aki.client = mocker.Mock(spec=httpx.Client)
    return aki
