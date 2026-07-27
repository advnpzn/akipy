from urllib.parse import urlparse

import httpx

from .dicts import ANSWER_MAP, HEADERS
from .exceptions import CloudflareBlockedError, InvalidChoiceError, SolverError
from .solver import (
    DEFAULT_SOLVER_TIMEOUT_MS,
    apply_solver_solution,
    async_solve_challenge,
    is_cloudflare_challenge,
    response_from_solution,
    solve_challenge,
)


def _site_origin(url: str) -> str:
    """Scheme + host root used for Cloudflare cookie harvest."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/"


def _merge_headers(client: httpx.Client | httpx.AsyncClient | None) -> dict[str, str]:
    """Merge default headers with client User-Agent after solver clearance.

    Keep the browser-like default User-Agent unless the client already has a
    non-httpx User-Agent (for example after a solver set it). Cloudflare blocks
    the stock ``python-httpx/...`` User-Agent.
    """
    headers = dict(HEADERS)
    if client is not None:
        try:
            ua = client.headers.get("User-Agent")
        except Exception:
            ua = None
        if ua and isinstance(ua, str) and not ua.startswith("python-httpx/"):
            headers["User-Agent"] = ua
    return headers


def _direct_request(
    client: httpx.Client,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    headers = kwargs.pop("headers", None) or _merge_headers(client)
    return client.request(method, url, headers=headers, **kwargs)


async def _async_direct_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    headers = kwargs.pop("headers", None) or _merge_headers(client)
    return await client.request(method, url, headers=headers, **kwargs)


def _resolve_solver_args(
    solver_url: str | None,
    solver_timeout: int | None,
    flaresolverr_url: str | None,
    flaresolverr_timeout: int | None,
) -> tuple[str | None, int]:
    """Prefer solver_* names; fall back to flaresolverr_* aliases."""
    url = solver_url if solver_url is not None else flaresolverr_url
    timeout = (
        solver_timeout
        if solver_timeout is not None
        else flaresolverr_timeout
        if flaresolverr_timeout is not None
        else DEFAULT_SOLVER_TIMEOUT_MS
    )
    return url, timeout


def _handle_cloudflare_sync(
    response: httpx.Response,
    *,
    url: str,
    method: str,
    data: dict | None,
    client: httpx.Client,
    request_kwargs: dict,
    solver_url: str | None,
    solver_timeout: int,
) -> httpx.Response:
    if not is_cloudflare_challenge(response):
        return response

    if not solver_url:
        raise CloudflareBlockedError()

    # 1) Prefer GET on site origin — FlareSolverr clears CF more reliably on GET;
    #    cookies + UA then allow the original POST/GET over plain httpx.
    origin = _site_origin(url)
    try:
        harvest = solve_challenge(
            solver_url=solver_url,
            url=origin,
            method="GET",
            data=None,
            max_timeout=solver_timeout,
        )
        apply_solver_solution(client, harvest)
        retry = _direct_request(client, method, url, **request_kwargs)
        if not is_cloudflare_challenge(retry):
            return retry
    except SolverError:
        pass

    # 2) Full original request through the solver
    solution = solve_challenge(
        solver_url=solver_url,
        url=url,
        method=method,
        data=data,
        max_timeout=solver_timeout,
    )
    apply_solver_solution(client, solution)

    retry = _direct_request(client, method, url, **request_kwargs)
    if not is_cloudflare_challenge(retry):
        return retry

    # Last resort: use the solver's already-fetched body
    return response_from_solution(solution, request=retry.request)


async def _handle_cloudflare_async(
    response: httpx.Response,
    *,
    url: str,
    method: str,
    data: dict | None,
    client: httpx.AsyncClient,
    request_kwargs: dict,
    solver_url: str | None,
    solver_timeout: int,
) -> httpx.Response:
    if not is_cloudflare_challenge(response):
        return response

    if not solver_url:
        raise CloudflareBlockedError()

    origin = _site_origin(url)
    try:
        harvest = await async_solve_challenge(
            solver_url=solver_url,
            url=origin,
            method="GET",
            data=None,
            max_timeout=solver_timeout,
        )
        apply_solver_solution(client, harvest)
        retry = await _async_direct_request(client, method, url, **request_kwargs)
        if not is_cloudflare_challenge(retry):
            return retry
    except SolverError:
        pass

    solution = await async_solve_challenge(
        solver_url=solver_url,
        url=url,
        method=method,
        data=data,
        max_timeout=solver_timeout,
    )
    apply_solver_solution(client, solution)

    retry = await _async_direct_request(client, method, url, **request_kwargs)
    if not is_cloudflare_challenge(retry):
        return retry

    return response_from_solution(solution, request=retry.request)


def request_handler(
    url: str,
    method: str,
    data: dict | None = None,
    client: httpx.Client | None = None,
    solver_url: str | None = None,
    solver_timeout: int | None = None,
    flaresolverr_url: str | None = None,
    flaresolverr_timeout: int | None = None,
    **kwargs,
) -> httpx.Response:
    """
    Sends an HTTP request to the specified URL using the provided method and data.

    When ``solver_url`` is set and the response is a Cloudflare challenge,
    solves once via that service (FlareSolverr, TRAWL, or other FlareSolverr
    v2-compatible API), injects cookies/User-Agent into ``client``, and retries
    over normal httpx.

    Parameters:
        url (str): The URL to send the request to.
        method (str): The HTTP method to use (e.g., 'GET', 'POST').
        data (dict, optional): The data to send with the request.
        client (httpx.Client, optional): An existing HTTP client to use.
        solver_url (str, optional): Normalized solver ``/v1`` endpoint.
        solver_timeout (int, optional): Solver ``maxTimeout`` in milliseconds.
        flaresolverr_url / flaresolverr_timeout: Aliases for solver_*.
        **kwargs: Additional keyword arguments to pass to the request.

    Returns:
        httpx.Response: The response from the server.
    """
    resolved_url, resolved_timeout = _resolve_solver_args(
        solver_url, solver_timeout, flaresolverr_url, flaresolverr_timeout
    )
    client = client or httpx.Client(timeout=30.0)
    request_kwargs = dict(kwargs)
    if data:
        request_kwargs["data"] = data
    try:
        response = _direct_request(client, method, url, **request_kwargs)
        response = _handle_cloudflare_sync(
            response,
            url=url,
            method=method,
            data=data,
            client=client,
            request_kwargs=request_kwargs,
            solver_url=resolved_url,
            solver_timeout=resolved_timeout,
        )
        response.raise_for_status()
        return response
    except (CloudflareBlockedError, SolverError):
        raise
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Request failed: {e}") from e


async def async_request_handler(
    url: str,
    method: str,
    data: dict | None = None,
    client: httpx.AsyncClient | None = None,
    solver_url: str | None = None,
    solver_timeout: int | None = None,
    flaresolverr_url: str | None = None,
    flaresolverr_timeout: int | None = None,
    **kwargs,
) -> httpx.Response:
    """
    Asynchronous variant of :func:`request_handler`.

    See :func:`request_handler` for solver behaviour (FlareSolverr / TRAWL / compatible).
    """
    resolved_url, resolved_timeout = _resolve_solver_args(
        solver_url, solver_timeout, flaresolverr_url, flaresolverr_timeout
    )
    client = client or httpx.AsyncClient(timeout=30.0)
    request_kwargs = dict(kwargs)
    if data:
        request_kwargs["data"] = data
    try:
        response = await _async_direct_request(client, method, url, **request_kwargs)
        response = await _handle_cloudflare_async(
            response,
            url=url,
            method=method,
            data=data,
            client=client,
            request_kwargs=request_kwargs,
            solver_url=resolved_url,
            solver_timeout=resolved_timeout,
        )
        response.raise_for_status()
        return response
    except (CloudflareBlockedError, SolverError):
        raise
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Request failed: {e}") from e


def get_answer_id(ans: str | int) -> int:
    """
    Converts an answer (either a string or an integer) to its corresponding answer ID.

    Parameters:
        ans (str | int): The answer to convert. Can be a string (e.g., 'yes', 'no') or an integer (0-4).

    Returns:
        int: The corresponding answer ID.

    Raises:
        InvalidChoiceError: If the answer is invalid.
    """
    if isinstance(ans, int):
        if ans not in range(5):
            raise InvalidChoiceError(f"Answer ID must be between 0 and 4, got {ans}")
        return ans
    ans2 = ANSWER_MAP.get(ans.lower())
    if ans2 is None:
        raise InvalidChoiceError(f"Invalid answer: {ans}")
    return ans2
