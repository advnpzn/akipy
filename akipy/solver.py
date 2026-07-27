"""
Cloudflare challenge solver helpers (FlareSolverr v2 API).

Works with any service that implements the FlareSolverr v2 ``POST /v1`` protocol,
including:

- `FlareSolverr <https://github.com/FlareSolverr/FlareSolverr>`_
- `TRAWL <https://github.com/germondai/trawl>`_ (and other compatible proxies)
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import httpx

from .exceptions import CloudflareBlockedError, SolverError

# FlareSolverr often needs >60s on cold CF challenges (CI datacenter IPs).
DEFAULT_SOLVER_TIMEOUT_MS = 120_000
DEFAULT_FLARESOLVERR_TIMEOUT_MS = DEFAULT_SOLVER_TIMEOUT_MS  # alias

_CF_BODY_MARKERS = (
    "just a moment",
    "cf-browser-verification",
    "challenge-platform",
    "attention required",
    "cdn-cgi/challenge",
    "cf-challenge",
    "checking your browser",
    "enable javascript and cookies",
)

_CF_STATUS_CODES = frozenset({403, 503})


def normalize_solver_url(url: str | None) -> str | None:
    """
    Normalize a challenge-solver base or ``/v1`` endpoint URL.

    Accepts local/remote hosts, with or without scheme, with or without ``/v1``.
    Defaults to ``http://`` when the scheme is omitted (HTTPS must be explicit).

    Compatible with FlareSolverr, TRAWL, and other FlareSolverr v2 API services.
    """
    if url is None:
        return None
    raw = url.strip()
    if not raw:
        return None

    raw = raw.rstrip("/")

    # Protocol-relative: //host:port
    if raw.startswith("//"):
        raw = "http:" + raw

    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "http://" + raw

    parsed = urlparse(raw)
    if not parsed.netloc:
        raise ValueError(f"Invalid solver URL: {url!r}")

    path = parsed.path.rstrip("/")
    if path.endswith("/v1"):
        path = path
    elif path == "" or path == "/":
        path = "/v1"
    else:
        path = path + "/v1"

    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


normalize_flaresolverr_url = normalize_solver_url  # alias


def is_cloudflare_challenge(response: httpx.Response) -> bool:
    """Return True if the response looks like a Cloudflare challenge or block page."""
    status = getattr(response, "status_code", None)
    headers = getattr(response, "headers", None) or {}
    try:
        server = headers.get("server", "").lower()
        has_cf_ray = "cf-ray" in headers
    except Exception:
        server = ""
        has_cf_ray = False

    try:
        body = response.text or ""
    except Exception:
        body = ""
    body_lower = body.lower() if isinstance(body, str) else ""
    has_body_marker = any(marker in body_lower for marker in _CF_BODY_MARKERS)

    if has_body_marker:
        return True

    if status in _CF_STATUS_CODES and (has_cf_ray or "cloudflare" in server):
        return True

    return False


def _encode_post_data(data: dict | None) -> str | None:
    if not data:
        return None
    return urlencode({str(k): str(v) for k, v in data.items()})


def _build_solver_payload(
    url: str,
    method: str,
    data: dict | None,
    max_timeout: int,
) -> dict[str, Any]:
    """Build a FlareSolverr v2-compatible request payload."""
    method_upper = method.upper()
    if method_upper == "GET":
        return {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": max_timeout,
        }
    if method_upper == "POST":
        payload: dict[str, Any] = {
            "cmd": "request.post",
            "url": url,
            "maxTimeout": max_timeout,
        }
        post_data = _encode_post_data(data)
        if post_data is not None:
            payload["postData"] = post_data
            # TRAWL requires Content-Type when postData is set (FlareSolverr is looser)
            payload["headers"] = {
                "Content-Type": "application/x-www-form-urlencoded",
            }
        return payload
    raise SolverError(
        f"Challenge solver only supports GET and POST, got {method_upper!r}"
    )


def apply_solver_solution(
    client: httpx.Client | httpx.AsyncClient,
    solution: dict[str, Any],
) -> None:
    """Inject solver cookies and User-Agent into a persistent httpx client."""
    user_agent = solution.get("userAgent")
    if user_agent:
        client.headers["User-Agent"] = user_agent

    cookies = solution.get("cookies") or []
    for cookie in cookies:
        name = cookie.get("name")
        value = cookie.get("value")
        if name is None or value is None:
            continue
        kwargs: dict[str, Any] = {}
        domain = cookie.get("domain")
        path = cookie.get("path")
        if domain:
            kwargs["domain"] = domain
        if path:
            kwargs["path"] = path
        client.cookies.set(name, value, **kwargs)


apply_flaresolverr_solution = apply_solver_solution  # alias


def _parse_solver_response(payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status")
    if status != "ok":
        message = payload.get("message") or payload.get("error") or str(payload)
        raise SolverError(f"Challenge solver failed: {message}")
    solution = payload.get("solution")
    if not isinstance(solution, dict):
        raise SolverError("Challenge solver response missing solution object")
    return solution


def solve_challenge(
    solver_url: str,
    url: str,
    method: str,
    data: dict | None = None,
    max_timeout: int = DEFAULT_SOLVER_TIMEOUT_MS,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """
    Call a FlareSolverr-compatible solver synchronously and return the solution dict.

    Works with FlareSolverr, TRAWL, and any other service implementing
    ``POST /v1`` with ``request.get`` / ``request.post`` commands.
    """
    payload = _build_solver_payload(url, method, data, max_timeout)
    owns_client = client is None
    solver_client = client or httpx.Client(timeout=max(max_timeout / 1000 + 30, 90))
    try:
        resp = solver_client.post(
            solver_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        # Prefer structured solver errors (e.g. TRAWL 400 JSON) over bare HTTP status
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = None
            if isinstance(body, dict) and body.get("status") == "error":
                message = body.get("message") or body.get("error") or resp.text
                raise SolverError(f"Challenge solver failed: {message}")
            resp.raise_for_status()
        return _parse_solver_response(resp.json())
    except SolverError:
        raise
    except Exception as e:
        raise SolverError(
            f"Failed to contact challenge solver at {solver_url}: {e}"
        ) from e
    finally:
        if owns_client:
            solver_client.close()


async def async_solve_challenge(
    solver_url: str,
    url: str,
    method: str,
    data: dict | None = None,
    max_timeout: int = DEFAULT_SOLVER_TIMEOUT_MS,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Call a FlareSolverr-compatible solver asynchronously and return the solution dict."""
    payload = _build_solver_payload(url, method, data, max_timeout)
    owns_client = client is None
    solver_client = client or httpx.AsyncClient(
        timeout=max(max_timeout / 1000 + 30, 90)
    )
    try:
        resp = await solver_client.post(
            solver_url,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code >= 400:
            try:
                body = resp.json()
            except Exception:
                body = None
            if isinstance(body, dict) and body.get("status") == "error":
                message = body.get("message") or body.get("error") or resp.text
                raise SolverError(f"Challenge solver failed: {message}")
            resp.raise_for_status()
        return _parse_solver_response(resp.json())
    except SolverError:
        raise
    except Exception as e:
        raise SolverError(
            f"Failed to contact challenge solver at {solver_url}: {e}"
        ) from e
    finally:
        if owns_client:
            await solver_client.aclose()


def solve_with_flaresolverr(
    flaresolverr_url: str,
    url: str,
    method: str,
    data: dict | None = None,
    max_timeout: int = DEFAULT_SOLVER_TIMEOUT_MS,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    return solve_challenge(flaresolverr_url, url, method, data, max_timeout, client)


async def async_solve_with_flaresolverr(
    flaresolverr_url: str,
    url: str,
    method: str,
    data: dict | None = None,
    max_timeout: int = DEFAULT_SOLVER_TIMEOUT_MS,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    return await async_solve_challenge(
        flaresolverr_url, url, method, data, max_timeout, client
    )


def response_from_solution(
    solution: dict[str, Any],
    request: httpx.Request | None = None,
) -> httpx.Response:
    """Build an httpx.Response from a solver solution (last-resort fallback)."""
    status = int(solution.get("status") or 200)
    body = solution.get("response") or ""
    if isinstance(body, bytes):
        content = body
    else:
        content = str(body).encode("utf-8", errors="replace")

    headers: dict[str, str] = {}
    sol_headers = solution.get("headers") or {}
    if isinstance(sol_headers, dict):
        headers = {str(k): str(v) for k, v in sol_headers.items()}

    return httpx.Response(
        status_code=status,
        headers=headers,
        content=content,
        request=request,
    )


def raise_if_cloudflare_blocked(
    response: httpx.Response,
    solver_url: str | None,
) -> None:
    """Raise CloudflareBlockedError when CF is detected and no solver is configured."""
    if is_cloudflare_challenge(response) and not solver_url:
        raise CloudflareBlockedError()
