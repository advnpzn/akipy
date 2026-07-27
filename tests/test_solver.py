"""Tests for challenge-solver URL normalization, CF detection, and fall-back."""

from unittest.mock import AsyncMock

import httpx
import pytest

from akipy import Akinator
from akipy.async_akinator import Akinator as AsyncAkinator
from akipy.exceptions import CloudflareBlockedError, FlareSolverrError, SolverError
from akipy._base import parse_api_json
from akipy.solver import (
    _build_solver_payload,
    apply_solver_solution,
    is_cloudflare_challenge,
    normalize_solver_url,
    response_from_solution,
)
from akipy.utils import async_request_handler, request_handler


class TestSolveChallengeNormalizesUrl:
    def test_posts_to_v1_endpoint(self, mocker):
        """Bare host URLs must hit /v1 (POST to / is 405 on FlareSolverr)."""
        mock_resp = mocker.Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status": "ok",
            "solution": {
                "status": 200,
                "response": "<html></html>",
                "cookies": [],
                "userAgent": "UA",
            },
        }
        mock_client = mocker.Mock()
        mock_client.post.return_value = mock_resp
        mock_client.__enter__ = mocker.Mock(return_value=mock_client)
        mock_client.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("akipy.solver.httpx.Client", return_value=mock_client)

        from akipy.solver import solve_challenge

        solve_challenge(
            "http://127.0.0.1:8191",
            "https://en.akinator.com/",
            "GET",
            max_timeout=1000,
        )
        assert mock_client.post.call_args[0][0] == "http://127.0.0.1:8191/v1"


class TestBuildSolverPayload:
    def test_get_payload(self):
        p = _build_solver_payload("https://example.com", "GET", None, 60000)
        assert p == {
            "cmd": "request.get",
            "url": "https://example.com",
            "maxTimeout": 60000,
        }

    def test_post_includes_content_type_for_trawl(self):
        p = _build_solver_payload(
            "https://en.akinator.com/game",
            "POST",
            {"sid": 1, "cm": "false"},
            60000,
        )
        assert p["cmd"] == "request.post"
        assert p["postData"] == "sid=1&cm=false"
        assert p["headers"]["Content-Type"] == "application/x-www-form-urlencoded"


class TestParseApiJson:
    def test_raw_json(self):
        data = parse_api_json('{"completion":"OK","step":"1"}')
        assert data["completion"] == "OK"
        assert data["step"] == "1"

    def test_browser_pre_wrapper(self):
        body = (
            '<html><head><meta name="color-scheme" content="light dark"></head>'
            '<body><pre>{"completion":"OK","step":"1","question":"Hi?"}</pre>'
            '<div class="json-formatter-container"></div></body></html>'
        )
        data = parse_api_json(body)
        assert data["question"] == "Hi?"
        assert data["step"] == "1"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            parse_api_json("   ")


class TestNormalizeSolverUrl:
    def test_none_and_empty(self):
        assert normalize_solver_url(None) is None
        assert normalize_solver_url("") is None
        assert normalize_solver_url("   ") is None

    def test_host_only_defaults_to_http_v1(self):
        assert normalize_solver_url("localhost:8191") == "http://localhost:8191/v1"
        assert normalize_solver_url("127.0.0.1:8191") == "http://127.0.0.1:8191/v1"

    def test_http_without_v1(self):
        assert (
            normalize_solver_url("http://localhost:8191") == "http://localhost:8191/v1"
        )

    def test_https_without_v1(self):
        assert (
            normalize_solver_url("https://fs.example.com")
            == "https://fs.example.com/v1"
        )

    def test_already_has_v1_no_double(self):
        assert (
            normalize_solver_url("https://fs.example.com/v1")
            == "https://fs.example.com/v1"
        )
        assert (
            normalize_solver_url("http://localhost:8191/v1/")
            == "http://localhost:8191/v1"
        )

    def test_protocol_relative(self):
        assert (
            normalize_solver_url("//fs.example.com:8191")
            == "http://fs.example.com:8191/v1"
        )

    def test_strips_whitespace_and_trailing_slash(self):
        assert (
            normalize_solver_url("  http://localhost:8191/  ")
            == "http://localhost:8191/v1"
        )


class TestIsCloudflareChallenge:
    def _response(self, status=200, text="", headers=None):
        return httpx.Response(
            status_code=status,
            headers=headers or {},
            content=text.encode("utf-8"),
            request=httpx.Request("GET", "https://en.akinator.com/game"),
        )

    def test_body_marker_just_a_moment(self):
        resp = self._response(
            status=200,
            text="<html>Just a moment...</html>",
            headers={"server": "cloudflare"},
        )
        assert is_cloudflare_challenge(resp) is True

    def test_403_with_cf_ray(self):
        resp = self._response(
            status=403,
            text="blocked",
            headers={"cf-ray": "abc123", "server": "cloudflare"},
        )
        assert is_cloudflare_challenge(resp) is True

    def test_503_with_cloudflare_server(self):
        resp = self._response(
            status=503,
            text="error",
            headers={"server": "cloudflare", "cf-ray": "xyz"},
        )
        assert is_cloudflare_challenge(resp) is True

    def test_normal_json_ok(self):
        resp = self._response(
            status=200,
            text='{"completion":"OK","question":"Is your character real?"}',
            headers={"content-type": "application/json"},
        )
        assert is_cloudflare_challenge(resp) is False

    def test_normal_html_game_page(self):
        resp = self._response(
            status=200,
            text="<html><body>$('#session').val('abc')</body></html>",
        )
        assert is_cloudflare_challenge(resp) is False

    def test_404_without_cf_not_challenge(self):
        resp = self._response(status=404, text="Not Found")
        assert is_cloudflare_challenge(resp) is False


class TestApplySolutionAndResponseFromSolution:
    def test_apply_cookies_and_user_agent(self):
        client = httpx.Client()
        solution = {
            "userAgent": "Mozilla/5.0 TestAgent",
            "cookies": [
                {
                    "name": "cf_clearance",
                    "value": "token123",
                    "domain": ".akinator.com",
                    "path": "/",
                }
            ],
        }
        apply_solver_solution(client, solution)
        assert client.headers["User-Agent"] == "Mozilla/5.0 TestAgent"
        assert client.cookies.get("cf_clearance") == "token123"
        client.close()

    def test_response_from_solution(self):
        solution = {
            "status": 200,
            "response": "<html>cleared</html>",
            "headers": {"content-type": "text/html"},
        }
        resp = response_from_solution(solution)
        assert resp.status_code == 200
        assert "cleared" in resp.text


class TestRequestHandlerCloudflare:
    def test_success_skips_solver(self, mocker):
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.headers = httpx.Headers()
        ok = httpx.Response(
            200,
            content=b'{"ok": true}',
            request=httpx.Request("GET", "https://example.com"),
        )
        mock_client.request.return_value = ok
        solve = mocker.patch("akipy.utils.solve_challenge")

        resp = request_handler(
            url="https://example.com",
            method="GET",
            client=mock_client,
            solver_url="http://localhost:8191/v1",
        )
        assert resp.status_code == 200
        solve.assert_not_called()
        assert mock_client.request.call_count == 1

    def test_cf_without_solver_raises(self, mocker):
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.headers = httpx.Headers()
        cf = httpx.Response(
            403,
            headers={"cf-ray": "x", "server": "cloudflare"},
            content=b"Just a moment...",
            request=httpx.Request("GET", "https://example.com"),
        )
        mock_client.request.return_value = cf

        with pytest.raises(CloudflareBlockedError):
            request_handler(
                url="https://example.com",
                method="GET",
                client=mock_client,
                solver_url=None,
            )

    def test_cf_with_solver_solves_and_retries(self, mocker):
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.headers = httpx.Headers()
        mock_client.cookies = httpx.Cookies()

        cf = httpx.Response(
            403,
            headers={"cf-ray": "x", "server": "cloudflare"},
            content=b"Just a moment...",
            request=httpx.Request("POST", "https://en.akinator.com/game"),
        )
        ok = httpx.Response(
            200,
            content=b"<html>session ok</html>",
            request=httpx.Request("POST", "https://en.akinator.com/game"),
        )
        mock_client.request.side_effect = [cf, ok]

        solution = {
            "status": 200,
            "userAgent": "Mozilla/5.0 Cleared",
            "cookies": [
                {
                    "name": "cf_clearance",
                    "value": "abc",
                    "domain": ".akinator.com",
                    "path": "/",
                }
            ],
            "response": "<html>from solver</html>",
        }
        solve = mocker.patch("akipy.utils.solve_challenge", return_value=solution)
        apply = mocker.patch("akipy.utils.apply_solver_solution")

        resp = request_handler(
            url="https://en.akinator.com/game",
            method="POST",
            data={"sid": "1", "cm": "false"},
            client=mock_client,
            solver_url="http://localhost:8191/v1",
            solver_timeout=30000,
        )

        assert resp.status_code == 200
        assert b"session ok" in resp.content
        solve.assert_called_once()
        apply.assert_called_once_with(mock_client, solution)
        assert mock_client.request.call_count == 2

    def test_flaresolverr_url_alias_works(self, mocker):
        """flaresolverr_url alias wires into the same path."""
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.headers = httpx.Headers()
        mock_client.cookies = httpx.Cookies()
        cf = httpx.Response(
            403,
            headers={"cf-ray": "x", "server": "cloudflare"},
            content=b"Just a moment...",
            request=httpx.Request("GET", "https://example.com"),
        )
        ok = httpx.Response(
            200,
            content=b"ok",
            request=httpx.Request("GET", "https://example.com"),
        )
        mock_client.request.side_effect = [cf, ok]
        mocker.patch(
            "akipy.utils.solve_challenge",
            return_value={"status": 200, "userAgent": "UA", "cookies": []},
        )
        mocker.patch("akipy.utils.apply_solver_solution")

        resp = request_handler(
            url="https://example.com",
            method="GET",
            client=mock_client,
            flaresolverr_url="http://localhost:8191/v1",
        )
        assert resp.status_code == 200

    def test_solver_error_propagates(self, mocker):
        mock_client = mocker.Mock(spec=httpx.Client)
        mock_client.headers = httpx.Headers()
        cf = httpx.Response(
            403,
            headers={"cf-ray": "x", "server": "cloudflare"},
            content=b"Just a moment...",
            request=httpx.Request("GET", "https://example.com"),
        )
        mock_client.request.return_value = cf
        mocker.patch(
            "akipy.utils.solve_challenge",
            side_effect=SolverError("solver down"),
        )

        with pytest.raises(SolverError, match="solver down"):
            request_handler(
                url="https://example.com",
                method="GET",
                client=mock_client,
                solver_url="http://localhost:8191/v1",
            )

    def test_flaresolverr_error_alias(self):
        assert FlareSolverrError is SolverError

    @pytest.mark.asyncio
    async def test_async_cf_with_solver_solves_and_retries(self, mocker):
        mock_client = mocker.Mock(spec=httpx.AsyncClient)
        mock_client.headers = httpx.Headers()
        mock_client.cookies = httpx.Cookies()

        cf = httpx.Response(
            403,
            headers={"cf-ray": "x", "server": "cloudflare"},
            content=b"Just a moment...",
            request=httpx.Request("POST", "https://en.akinator.com/game"),
        )
        ok = httpx.Response(
            200,
            content=b'{"completion":"OK"}',
            request=httpx.Request("POST", "https://en.akinator.com/game"),
        )
        mock_client.request = AsyncMock(side_effect=[cf, ok])

        solution = {
            "status": 200,
            "userAgent": "Mozilla/5.0 Cleared",
            "cookies": [{"name": "cf_clearance", "value": "abc"}],
            "response": "{}",
        }
        mocker.patch(
            "akipy.utils.async_solve_challenge",
            new=AsyncMock(return_value=solution),
        )
        mocker.patch("akipy.utils.apply_solver_solution")

        resp = await async_request_handler(
            url="https://en.akinator.com/game",
            method="POST",
            data={"sid": "1"},
            client=mock_client,
            solver_url="http://localhost:8191/v1",
        )
        assert resp.status_code == 200
        assert mock_client.request.await_count == 2


class TestAkinatorConstructor:
    def test_default_no_solver(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        aki = Akinator()
        assert aki.solver_url is None
        assert aki.flaresolverr_url is None

    def test_constructor_normalizes_url(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        aki = Akinator(solver_url="localhost:8191")
        assert aki.solver_url == "http://localhost:8191/v1"
        assert aki.flaresolverr_url == aki.solver_url

    def test_env_solver_url(self, monkeypatch):
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        monkeypatch.setenv("AKIPY_SOLVER_URL", "http://remote:8191")
        aki = Akinator()
        assert aki.solver_url == "http://remote:8191/v1"

    def test_env_flaresolverr_fallback(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.setenv("AKIPY_FLARESOLVERR_URL", "http://legacy:8191")
        aki = Akinator()
        assert aki.solver_url == "http://legacy:8191/v1"

    def test_constructor_overrides_env(self, monkeypatch):
        monkeypatch.setenv("AKIPY_SOLVER_URL", "http://env:8191")
        aki = Akinator(solver_url="http://arg:8191")
        assert aki.solver_url == "http://arg:8191/v1"

    def test_flaresolverr_url_alias(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        aki = Akinator(flaresolverr_url="http://legacy:8191")
        assert aki.solver_url == "http://legacy:8191/v1"

    def test_async_constructor(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        aki = AsyncAkinator(solver_url="https://trawl.example.com/v1")
        assert aki.solver_url == "https://trawl.example.com/v1"

    def test_custom_timeout(self, monkeypatch):
        monkeypatch.delenv("AKIPY_SOLVER_URL", raising=False)
        monkeypatch.delenv("AKIPY_FLARESOLVERR_URL", raising=False)
        aki = Akinator(solver_url="http://localhost:8191", solver_timeout=120000)
        assert aki.solver_url == "http://localhost:8191/v1"
        assert aki.solver_timeout == 120000
