import httpx

from .dicts import ANSWER_MAP, generate_headers
from .exceptions import InvalidChoiceError


def _make_response(text: str, content_type: str = "application/json") -> httpx.Response:
    request = httpx.Request("POST", "https://en.akinator.com")
    return httpx.Response(
        status_code=200,
        text=text,
        headers={"content-type": content_type},
        request=request,
    )


def _extract_json_from_html(text: str) -> str:
    if "<html" in text.lower() and "<pre" in text.lower():
        import re as _re

        json_match = _re.search(r"<pre>(.*?)</pre>", text, _re.DOTALL)
        if json_match:
            return json_match.group(1)
    return text


def request_handler(
    url: str,
    method: str,
    data: dict | None = None,
    client: httpx.Client | None = None,
    **kwargs,
) -> httpx.Response:
    client = client or httpx.Client(timeout=30.0)
    headers = generate_headers()
    if data:
        kwargs["data"] = data
    try:
        response = client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Request failed: {e}")


async def async_request_handler(
    url: str,
    method: str,
    data: dict | None = None,
    client: httpx.AsyncClient | None = None,
    **kwargs,
) -> httpx.Response:
    client = client or httpx.AsyncClient(timeout=30.0)
    headers = generate_headers()
    if data:
        kwargs["data"] = data
    try:
        response = await client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response
    except httpx.HTTPError as e:
        raise httpx.HTTPError(f"Request failed: {e}")


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
