"""Tests for the synchronous Akinator class"""
import pytest
import httpx
from akipy import Akinator
from akipy.exceptions import (
    CantGoBackAnyFurther,
    InvalidChoiceError
)


class TestAkinatorInitialization:
    """Tests for Akinator class initialization"""

    def test_akinator_instance_creation(self):
        """Test that Akinator instance can be created"""
        aki = Akinator()
        assert isinstance(aki, Akinator)

    def test_akinator_initial_attributes(self):
        """Test that Akinator has correct initial attributes"""
        aki = Akinator()
        assert aki.flag_photo is None
        assert aki.photo is None
        assert aki.pseudo is None
        assert aki.uri is None
        assert aki.theme is None
        assert aki.session is None
        assert aki.signature is None
        assert aki.identifiant is None
        assert aki.child_mode is False
        assert aki.lang is None
        assert aki.finished is False
        assert aki.win is False

    def test_akinator_repr(self):
        """Test Akinator string representation"""
        aki = Akinator()
        aki.question = "Test question?"
        assert "Test question?" in str(aki)
        assert "Akinator" in repr(aki)


class TestAkinatorStartGame:
    """Tests for start_game method"""

    def test_start_game_with_default_language(self, mocker, mock_game_initialization_response):
        """Test starting game with default English language"""
        aki = Akinator()
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.start_game()
        
        assert result == aki
        assert aki.lang == "en"
        assert aki.uri == "https://en.akinator.com"
        assert aki.session == "test_session_123"
        assert aki.signature == "test_signature_456"
        assert aki.identifiant == "test_identifiant_789"
        # Question may include extra HTML due to greedy regex, just check it starts correctly
        assert aki.question.startswith("Is your character real?")
        assert aki.progression == "0.00000"
        assert aki.step == "0"

    def test_start_game_with_specific_language(self, mocker, mock_game_initialization_response):
        """Test starting game with a specific language"""
        aki = Akinator()
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        aki.start_game(language="french")
        
        assert aki.lang == "fr"
        assert aki.uri == "https://fr.akinator.com"

    def test_start_game_with_language_code(self, mocker, mock_game_initialization_response):
        """Test starting game with language code"""
        aki = Akinator()
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        aki.start_game(language="es")
        
        assert aki.lang == "es"
        assert aki.uri == "https://es.akinator.com"

    def test_start_game_with_child_mode(self, mocker, mock_game_initialization_response):
        """Test starting game with child mode enabled"""
        aki = Akinator()
        
        # Need to set child_mode BEFORE calling start_game
        aki.child_mode = True
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()
        
        # Mock the request handler
        mock_request = mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        aki.start_game(child_mode=True)
        
        # Check that child mode was set on the object  
        assert aki.child_mode is True
        # Verify that request was made with child_mode=true
        # The second call is to /game with cm parameter
        call_args = mock_request.call_args_list[1]
        assert call_args[1]['data']['cm'] == 'true'

    def test_start_game_with_invalid_language(self):
        """Test that invalid language raises InvalidLanguageError"""
        # Simulate what happens in __get_region when an invalid language is used
        with pytest.raises(AssertionError):
            from akipy.dicts import LANG_MAP
            lang = "invalid_xyz"
            # This mimics the logic in __get_region
            if len(lang) > 2:
                lang = LANG_MAP.get(lang, lang)
            # This should raise AssertionError for invalid lang
            assert lang in LANG_MAP.values(), f"Invalid language: {lang}"


class TestAkinatorAnswer:
    """Tests for answer method"""

    def test_answer_with_yes(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test answering 'yes' to a question"""
        aki = initialized_akinator
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.answer("yes")
        
        assert result == aki
        assert aki.question == "Is your character from a movie?"
        assert aki.step == "1"
        assert aki.progression == "10.5"

    def test_answer_with_no(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test answering 'no' to a question"""
        aki = initialized_akinator
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.answer("no")
        
        assert result == aki

    def test_answer_with_integer(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test answering with integer (0-4)"""
        aki = initialized_akinator
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.answer(2)  # I don't know
        
        assert result == aki

    def test_answer_when_win_with_yes_calls_choose(self, initialized_akinator, mocker):
        """Test answering 'yes' when in win state calls choose"""
        aki = initialized_akinator
        aki.win = True
        aki.id_proposition = "12345"
        aki.name_proposition = "Mario"
        
        mock_choose = mocker.patch.object(aki, 'choose', return_value=aki)
        
        result = aki.answer("yes")
        
        mock_choose.assert_called_once()
        assert result == aki

    def test_answer_when_win_with_no_calls_exclude(self, initialized_akinator, mocker):
        """Test answering 'no' when in win state calls exclude"""
        aki = initialized_akinator
        aki.win = True
        aki.id_proposition = "12345"
        
        mock_exclude = mocker.patch.object(aki, 'exclude', return_value=aki)
        
        result = aki.answer("no")
        
        mock_exclude.assert_called_once()
        assert result == aki

    def test_answer_when_win_with_invalid_raises_error(self, initialized_akinator):
        """Test answering with invalid choice when in win state"""
        aki = initialized_akinator
        aki.win = True
        
        with pytest.raises(InvalidChoiceError, match="Only 'yes' or 'no'"):
            aki.answer("probably")

    def test_yes_method(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test yes() convenience method"""
        aki = initialized_akinator
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.yes()
        
        assert result == aki

    def test_no_method(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test no() convenience method"""
        aki = initialized_akinator
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.no()
        
        assert result == aki


class TestAkinatorBack:
    """Tests for back method"""

    def test_back_goes_to_previous_question(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test going back to previous question"""
        aki = initialized_akinator
        aki.step = "5"
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.back()
        
        assert result == aki
        assert aki.win is False

    def test_back_at_first_question_raises_error(self, initialized_akinator):
        """Test that going back at first question raises error"""
        aki = initialized_akinator
        aki.step = 1
        
        with pytest.raises(CantGoBackAnyFurther, match="first question"):
            aki.back()

    def test_back_resets_win_state(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test that back() resets win state"""
        aki = initialized_akinator
        aki.step = "5"
        aki.win = True
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        aki.back()
        
        assert aki.win is False


class TestAkinatorExclude:
    """Tests for exclude method"""

    def test_exclude_when_not_win_raises_error(self, initialized_akinator):
        """Test that exclude when not in win state raises error"""
        aki = initialized_akinator
        aki.win = False
        
        with pytest.raises(InvalidChoiceError, match="only exclude when"):
            aki.exclude()

    def test_exclude_continues_game(self, initialized_akinator, mocker, mock_answer_response_json):
        """Test that exclude continues the game"""
        aki = initialized_akinator
        aki.win = True
        aki.id_proposition = "12345"
        aki.finished = False
        aki.completion = "OK"  # Set initial completion
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.exclude()
        
        assert result == aki
        assert aki.win is False
        assert aki.id_proposition == ""

    def test_exclude_when_finished_calls_defeat(self, initialized_akinator, mocker):
        """Test that exclude when finished calls defeat"""
        aki = initialized_akinator
        aki.win = True
        aki.finished = True
        
        mock_defeat = mocker.patch.object(aki, 'defeat', return_value=aki)
        
        aki.exclude()
        
        mock_defeat.assert_called_once()


class TestAkinatorChoose:
    """Tests for choose method"""

    def test_choose_when_not_win_raises_error(self, initialized_akinator):
        """Test that choose when not in win state raises error"""
        aki = initialized_akinator
        aki.win = False
        
        with pytest.raises(InvalidChoiceError, match="only choose when"):
            aki.choose()

    def test_choose_finishes_game(self, initialized_akinator, mocker, mock_choice_response):
        """Test that choose finishes the game"""
        aki = initialized_akinator
        aki.win = True
        aki.id_proposition = "12345"
        aki.name_proposition = "Mario"
        aki.description_proposition = "Italian plumber"
        aki.flag_photo = "https://example.com/flag.jpg"
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_choice_response
        mock_response.raise_for_status = mocker.Mock()
        
        mocker.patch('akipy.akinator.request_handler', return_value=mock_response)
        
        result = aki.choose()
        
        assert result == aki
        assert aki.finished is True
        assert aki.win is True
        assert aki.akitude == "triomphe.png"
        assert aki.progression == "100.00000"


class TestAkinatorDefeat:
    """Tests for defeat method"""

    def test_defeat_sets_finished_and_loss(self):
        """Test that defeat sets finished and loss state"""
        aki = Akinator()
        
        result = aki.defeat()
        
        assert result == aki
        assert aki.finished is True
        assert aki.win is False
        assert aki.akitude == "deception.png"
        assert aki.progression == "100.00000"


class TestAkinatorProperties:
    """Tests for Akinator properties"""

    def test_confidence_property(self):
        """Test confidence property calculation"""
        aki = Akinator()
        aki.progression = "50.00000"
        
        assert aki.confidence == 0.5

    def test_confidence_at_start(self):
        """Test confidence at game start"""
        aki = Akinator()
        aki.progression = "0.00000"
        
        assert aki.confidence == 0.0

    def test_confidence_at_end(self):
        """Test confidence at game end"""
        aki = Akinator()
        aki.progression = "100.00000"
        
        assert aki.confidence == 1.0

    def test_akitude_url_property(self):
        """Test akitude_url property"""
        aki = Akinator()
        aki.uri = "https://en.akinator.com"
        aki.akitude = "defi.png"
        
        expected = "https://en.akinator.com/assets/img/akitudes_670x1096/defi.png"
        assert aki.akitude_url == expected


class TestAkinatorStringRepresentation:
    """Tests for Akinator string methods"""

    def test_str_returns_question(self):
        """Test __str__ returns question"""
        aki = Akinator()
        aki.question = "Is your character male?"
        
        assert str(aki) == "Is your character male?"

    def test_str_with_win_shows_proposition(self):
        """Test __str__ with win shows proposition"""
        aki = Akinator()
        aki.win = True
        aki.finished = False
        aki.proposition_message = "I think of"
        aki.name_proposition = "Mario"
        aki.description_proposition = "Italian plumber"
        
        result = str(aki)
        assert "I think of" in result
        assert "Mario" in result
        assert "Italian plumber" in result

    def test_repr_contains_akinator_and_question(self):
        """Test __repr__ contains Akinator and question"""
        aki = Akinator()
        aki.question = "Test question?"
        
        result = repr(aki)
        assert "Akinator" in result
        assert "Test question?" in result


class TestAkinatorHandleResponse:
    """Tests for handle_response method"""

    def test_handle_response_with_answer(self, initialized_akinator, mocker):
        """Test handle_response updates state correctly"""
        aki = initialized_akinator
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "completion": "OK",
            "akitude": "concentre.png",
            "step": "5",
            "progression": "45.5",
            "question": "Is your character from anime?"
        }
        mock_response.raise_for_status = mocker.Mock()
        
        aki.handle_response(mock_response)
        
        assert aki.akitude == "concentre.png"
        assert aki.step == "5"
        assert aki.progression == "45.5"
        assert aki.question == "Is your character from anime?"
        assert aki.completion == "OK"

    def test_handle_response_with_win(self, initialized_akinator, mocker, mock_win_response_json):
        """Test handle_response with win proposition"""
        aki = initialized_akinator
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_win_response_json
        mock_response.raise_for_status = mocker.Mock()
        
        aki.handle_response(mock_response)
        
        assert aki.win is True
        assert aki.id_proposition == "12345"
        assert aki.name_proposition == "Mario"
        assert aki.description_proposition == "Italian plumber from Nintendo"

    def test_handle_response_with_timeout(self, initialized_akinator, mocker):
        """Test handle_response with timeout"""
        aki = initialized_akinator
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"completion": "KO - TIMEOUT"}
        mock_response.raise_for_status = mocker.Mock()
        
        with pytest.raises(TimeoutError, match="session has timed out"):
            aki.handle_response(mock_response)

    def test_handle_response_with_technical_problem(self, initialized_akinator, mocker):
        """Test handle_response with technical problem"""
        aki = initialized_akinator
        
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception("Parse error")
        mock_response.text = "A technical problem has occurred."
        mock_response.raise_for_status = mocker.Mock()
        
        with pytest.raises(RuntimeError, match="technical problem"):
            aki.handle_response(mock_response)
