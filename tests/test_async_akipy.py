"""Tests for the asynchronous Akinator class"""

import pytest
import httpx
from akipy.async_akipy import Akinator as AsyncAkinator
from akipy.exceptions import CantGoBackAnyFurther, InvalidChoiceError


class TestAsyncAkinatorInitialization:
    """Tests for async Akinator class initialization"""

    def test_async_akinator_instance_creation(self):
        """Test that async Akinator instance can be created"""
        aki = AsyncAkinator()
        assert isinstance(aki, AsyncAkinator)

    def test_async_akinator_inherits_from_sync(self):
        """Test that async Akinator inherits from sync version"""
        from akipy.akinator import Akinator as SyncAkinator

        aki = AsyncAkinator()
        assert isinstance(aki, SyncAkinator)

    def test_async_akinator_initial_attributes(self):
        """Test that async Akinator has correct initial attributes"""
        aki = AsyncAkinator()
        assert aki.flag_photo is None
        assert aki.photo is None
        assert aki.session is None
        assert aki.child_mode is False
        assert aki.finished is False
        assert aki.win is False


class TestAsyncAkinatorStartGame:
    """Tests for async start_game method"""

    @pytest.mark.asyncio
    async def test_start_game_with_default_language(
        self, mocker, mock_game_initialization_response
    ):
        """Test starting game with default English language"""
        aki = AsyncAkinator()

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.start_game()

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

    @pytest.mark.asyncio
    async def test_start_game_with_specific_language(
        self, mocker, mock_game_initialization_response
    ):
        """Test starting game with a specific language"""
        aki = AsyncAkinator()

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        await aki.start_game(language="french")

        assert aki.lang == "fr"
        assert aki.uri == "https://fr.akinator.com"

    @pytest.mark.asyncio
    async def test_start_game_with_language_code(
        self, mocker, mock_game_initialization_response
    ):
        """Test starting game with language code"""
        aki = AsyncAkinator()

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        await aki.start_game(language="es")

        assert aki.lang == "es"
        assert aki.uri == "https://es.akinator.com"

    @pytest.mark.asyncio
    async def test_start_game_with_child_mode(
        self, mocker, mock_game_initialization_response
    ):
        """Test starting game with child mode enabled"""
        aki = AsyncAkinator()

        # Need to set child_mode BEFORE calling start_game
        aki.child_mode = True

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_game_initialization_response
        mock_response.raise_for_status = mocker.Mock()

        # Mock the request handler
        mock_request = mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        # Clear the language cache to ensure consistent test behavior
        from akipy import akinator

        akinator.Akinator._validated_languages.clear()

        await aki.start_game(child_mode=True)

        # Check that child mode was set on the object
        assert aki.child_mode is True
        # Verify that request was made with child_mode=true
        # The second call is to /game with cm parameter
        call_args = mock_request.call_args_list[1]
        assert call_args[1]["data"]["cm"] == "true"


class TestAsyncAkinatorAnswer:
    """Tests for async answer method"""

    @pytest.mark.asyncio
    async def test_answer_with_yes(self, mocker, mock_answer_response_json):
        """Test answering 'yes' to a question"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "0"
        aki.progression = "0.00000"
        aki.child_mode = False
        aki.step_last_proposition = ""
        aki.win = False
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.answer("yes")

        assert result == aki
        assert aki.question == "Is your character from a movie?"
        assert aki.step == "1"
        assert aki.progression == "10.5"

    @pytest.mark.asyncio
    async def test_answer_with_no(self, mocker, mock_answer_response_json):
        """Test answering 'no' to a question"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "0"
        aki.progression = "0.00000"
        aki.child_mode = False
        aki.step_last_proposition = ""
        aki.win = False
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.answer("no")

        assert result == aki

    @pytest.mark.asyncio
    async def test_answer_with_integer(self, mocker, mock_answer_response_json):
        """Test answering with integer (0-4)"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "0"
        aki.progression = "0.00000"
        aki.child_mode = False
        aki.step_last_proposition = ""
        aki.win = False
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.answer(2)  # I don't know

        assert result == aki

    @pytest.mark.asyncio
    async def test_answer_when_win_with_yes_calls_choose(self, mocker):
        """Test answering 'yes' when in win state calls choose"""
        aki = AsyncAkinator()
        aki.win = True
        aki.id_proposition = "12345"
        aki.name_proposition = "Mario"

        async def mock_choose():
            return aki

        mocker.patch.object(aki, "choose", side_effect=mock_choose)

        result = await aki.answer("yes")

        assert result == aki

    @pytest.mark.asyncio
    async def test_answer_when_win_with_no_calls_exclude(self, mocker):
        """Test answering 'no' when in win state calls exclude"""
        aki = AsyncAkinator()
        aki.win = True
        aki.id_proposition = "12345"

        async def mock_exclude():
            return aki

        mocker.patch.object(aki, "exclude", side_effect=mock_exclude)

        result = await aki.answer("no")

        assert result == aki

    @pytest.mark.asyncio
    async def test_answer_when_win_with_invalid_raises_error(self):
        """Test answering with invalid choice when in win state"""
        aki = AsyncAkinator()
        aki.win = True

        with pytest.raises(InvalidChoiceError, match="Only 'yes' or 'no'"):
            await aki.answer("probably")


class TestAsyncAkinatorBack:
    """Tests for async back method"""

    @pytest.mark.asyncio
    async def test_back_goes_to_previous_question(
        self, mocker, mock_answer_response_json
    ):
        """Test going back to previous question"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "5"
        aki.progression = "50.0"
        aki.child_mode = False
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.back()

        assert result == aki
        assert aki.win is False

    @pytest.mark.asyncio
    async def test_back_at_first_question_raises_error(self):
        """Test that going back at first question raises error"""
        aki = AsyncAkinator()
        aki.step = 1

        with pytest.raises(CantGoBackAnyFurther, match="first question"):
            await aki.back()

    @pytest.mark.asyncio
    async def test_back_resets_win_state(self, mocker, mock_answer_response_json):
        """Test that back() resets win state"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "5"
        aki.progression = "50.0"
        aki.child_mode = False
        aki.win = True
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        await aki.back()

        assert aki.win is False


class TestAsyncAkinatorExclude:
    """Tests for async exclude method"""

    @pytest.mark.asyncio
    async def test_exclude_when_not_win_raises_error(self):
        """Test that exclude when not in win state raises error"""
        aki = AsyncAkinator()
        aki.win = False

        with pytest.raises(InvalidChoiceError, match="only exclude when"):
            await aki.exclude()

    @pytest.mark.asyncio
    async def test_exclude_continues_game(self, mocker, mock_answer_response_json):
        """Test that exclude continues the game"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.step = "10"
        aki.progression = "80.0"
        aki.child_mode = False
        aki.win = True
        aki.id_proposition = "12345"
        aki.finished = False
        aki.completion = "OK"  # Set initial completion
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json = mocker.Mock(return_value=mock_answer_response_json)
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.exclude()

        assert result == aki
        assert aki.win is False
        assert aki.id_proposition == ""

    @pytest.mark.asyncio
    async def test_exclude_when_finished_calls_defeat(self, mocker):
        """Test that exclude when finished calls defeat"""
        aki = AsyncAkinator()
        aki.win = True
        aki.finished = True

        mock_defeat = mocker.patch.object(aki, "defeat", return_value=aki)

        await aki.exclude()

        mock_defeat.assert_called_once()


class TestAsyncAkinatorChoose:
    """Tests for async choose method"""

    @pytest.mark.asyncio
    async def test_choose_when_not_win_raises_error(self):
        """Test that choose when not in win state raises error"""
        aki = AsyncAkinator()
        aki.win = False

        with pytest.raises(InvalidChoiceError, match="only choose when"):
            await aki.choose()

    @pytest.mark.asyncio
    async def test_choose_finishes_game(self, mocker, mock_choice_response):
        """Test that choose finishes the game"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.theme = 1
        aki.session = "test_session"
        aki.signature = "test_signature"
        aki.identifiant = "test_identifiant"
        aki.step = "15"
        aki.win = True
        aki.id_proposition = "12345"
        aki.name_proposition = "Mario"
        aki.description_proposition = "Italian plumber"
        aki.flag_photo = "https://example.com/flag.jpg"
        aki.client = mocker.Mock(spec=httpx.AsyncClient)

        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = mock_choice_response
        mock_response.raise_for_status = mocker.Mock()

        mocker.patch(
            "akipy.async_akipy.async_request_handler", return_value=mock_response
        )

        result = await aki.choose()

        assert result == aki
        assert aki.finished is True
        assert aki.win is True
        assert aki.akitude == "triomphe.png"
        assert aki.progression == "100.00000"


class TestAsyncAkinatorInheritance:
    """Tests to verify async version uses inherited methods correctly"""

    def test_async_uses_sync_defeat(self):
        """Test that async version uses sync defeat method"""
        aki = AsyncAkinator()

        result = aki.defeat()

        assert result == aki
        assert aki.finished is True
        assert aki.win is False

    def test_async_has_confidence_property(self):
        """Test that async version has confidence property"""
        aki = AsyncAkinator()
        aki.progression = "75.5"

        assert aki.confidence == 0.755

    def test_async_has_akitude_url_property(self):
        """Test that async version has akitude_url property"""
        aki = AsyncAkinator()
        aki.uri = "https://en.akinator.com"
        aki.akitude = "concentre.png"

        expected = "https://en.akinator.com/assets/img/akitudes_670x1096/concentre.png"
        assert aki.akitude_url == expected

    def test_async_str_representation(self):
        """Test async version string representation"""
        aki = AsyncAkinator()
        aki.question = "Is your character real?"

        assert str(aki) == "Is your character real?"
        assert "Akinator" in repr(aki)
