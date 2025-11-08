"""Tests for utility functions"""

import pytest
import httpx
from akipy.utils import get_answer_id, request_handler, async_request_handler
from akipy.exceptions import InvalidChoiceError


class TestGetAnswerId:
    """Tests for get_answer_id function"""

    def test_get_answer_id_with_yes_variations(self):
        """Test that 'yes' variations return 0"""
        assert get_answer_id("yes") == 0
        assert get_answer_id("YES") == 0
        assert get_answer_id("Yes") == 0
        assert get_answer_id("y") == 0
        assert get_answer_id("Y") == 0
        assert get_answer_id("0") == 0

    def test_get_answer_id_with_no_variations(self):
        """Test that 'no' variations return 1"""
        assert get_answer_id("no") == 1
        assert get_answer_id("NO") == 1
        assert get_answer_id("No") == 1
        assert get_answer_id("n") == 1
        assert get_answer_id("N") == 1
        assert get_answer_id("1") == 1

    def test_get_answer_id_with_idk_variations(self):
        """Test that 'I don't know' variations return 2"""
        assert get_answer_id("i") == 2
        assert get_answer_id("idk") == 2
        assert get_answer_id("i dont know") == 2
        assert get_answer_id("i don't know") == 2
        assert get_answer_id("2") == 2

    def test_get_answer_id_with_probably_variations(self):
        """Test that 'probably' variations return 3"""
        assert get_answer_id("p") == 3
        assert get_answer_id("probably") == 3
        assert get_answer_id("PROBABLY") == 3
        assert get_answer_id("3") == 3

    def test_get_answer_id_with_probably_not_variations(self):
        """Test that 'probably not' variations return 4"""
        assert get_answer_id("pn") == 4
        assert get_answer_id("probably not") == 4
        assert get_answer_id("PROBABLY NOT") == 4
        assert get_answer_id("4") == 4

    def test_get_answer_id_with_integer_input(self):
        """Test that integer inputs (0-4) are returned as-is"""
        assert get_answer_id(0) == 0
        assert get_answer_id(1) == 1
        assert get_answer_id(2) == 2
        assert get_answer_id(3) == 3
        assert get_answer_id(4) == 4

    def test_get_answer_id_with_invalid_integer(self):
        """Test that invalid integers raise InvalidChoiceError"""
        with pytest.raises(
            InvalidChoiceError, match="Answer ID must be between 0 and 4"
        ):
            get_answer_id(5)
        with pytest.raises(
            InvalidChoiceError, match="Answer ID must be between 0 and 4"
        ):
            get_answer_id(-1)
        with pytest.raises(
            InvalidChoiceError, match="Answer ID must be between 0 and 4"
        ):
            get_answer_id(10)

    def test_get_answer_id_with_invalid_string(self):
        """Test that invalid strings raise InvalidChoiceError"""
        with pytest.raises(InvalidChoiceError, match="Invalid answer"):
            get_answer_id("invalid")
        with pytest.raises(InvalidChoiceError, match="Invalid answer"):
            get_answer_id("maybe")
        with pytest.raises(InvalidChoiceError, match="Invalid answer"):
            get_answer_id("")


class TestRequestHandler:
    """Tests for request_handler function"""

    def test_request_handler_get_request(self, mocker):
        """Test GET request without data"""
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()
        mock_client.request.return_value = mock_response

        result = request_handler(
            url="https://example.com", method="GET", client=mock_client
        )

        assert result == mock_response
        mock_client.request.assert_called_once()
        mock_response.raise_for_status.assert_called_once()

    def test_request_handler_post_request_with_data(self, mocker):
        """Test POST request with data"""
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()
        mock_client.request.return_value = mock_response

        data = {"key": "value"}
        result = request_handler(
            url="https://example.com", method="POST", data=data, client=mock_client
        )

        assert result == mock_response
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["data"] == data

    def test_request_handler_creates_client_if_none_provided(self, mocker):
        """Test that a client is created if none is provided"""
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()

        mock_client_instance = mocker.Mock(spec=httpx.Client)
        mock_client_instance.request.return_value = mock_response

        mocker.patch("akipy.utils.httpx.Client", return_value=mock_client_instance)

        result = request_handler(url="https://example.com", method="GET")

        assert result == mock_response

    def test_request_handler_raises_http_error(self, mocker):
        """Test that HTTPError is raised on request failure"""
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.request.side_effect = httpx.HTTPError("Connection failed")

        with pytest.raises(httpx.HTTPError, match="Request failed"):
            request_handler(url="https://example.com", method="GET", client=mock_client)

    def test_request_handler_with_additional_kwargs(self, mocker):
        """Test that additional kwargs are passed through"""
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()
        mock_client.request.return_value = mock_response

        request_handler(
            url="https://example.com",
            method="GET",
            client=mock_client,
            follow_redirects=True,
        )

        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["follow_redirects"] is True


class TestAsyncRequestHandler:
    """Tests for async_request_handler function"""

    @pytest.mark.asyncio
    async def test_async_request_handler_get_request(self, mocker):
        """Test async GET request"""
        mock_client = mocker.Mock(spec=httpx.AsyncClient)
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()
        mock_client.request = mocker.AsyncMock(return_value=mock_response)

        result = await async_request_handler(
            url="https://example.com", method="GET", client=mock_client
        )

        assert result == mock_response
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_request_handler_post_with_data(self, mocker):
        """Test async POST request with data"""
        mock_client = mocker.Mock(spec=httpx.AsyncClient)
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()
        mock_client.request = mocker.AsyncMock(return_value=mock_response)

        data = {"key": "value"}
        result = await async_request_handler(
            url="https://example.com", method="POST", data=data, client=mock_client
        )

        assert result == mock_response
        call_kwargs = mock_client.request.call_args[1]
        assert call_kwargs["data"] == data

    @pytest.mark.asyncio
    async def test_async_request_handler_creates_client_if_none(self, mocker):
        """Test that async client is created if none provided"""
        mock_response = mocker.Mock(spec=httpx.Response)
        mock_response.raise_for_status = mocker.Mock()

        mock_client_instance = mocker.Mock(spec=httpx.AsyncClient)
        mock_client_instance.request = mocker.AsyncMock(return_value=mock_response)

        mocker.patch("akipy.utils.httpx.AsyncClient", return_value=mock_client_instance)

        result = await async_request_handler(url="https://example.com", method="GET")

        assert result == mock_response

    @pytest.mark.asyncio
    async def test_async_request_handler_raises_http_error(self, mocker):
        """Test that HTTPError is raised on async request failure"""
        mock_client = mocker.Mock(spec=httpx.AsyncClient)
        mock_client.request = mocker.AsyncMock(
            side_effect=httpx.HTTPError("Connection failed")
        )

        with pytest.raises(httpx.HTTPError, match="Request failed"):
            await async_request_handler(
                url="https://example.com", method="GET", client=mock_client
            )
