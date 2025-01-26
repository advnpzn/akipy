import httpx

from .dicts import ANSWER_MAP, HEADERS
from .exceptions import InvalidChoiceError


def request_handler(
    url: str,
    method: str,
    data: dict | None = None,
    client: httpx.Client | None = None,
    **kwargs,
) -> httpx.Response:
    """
    Sends an HTTP request to the specified URL using the provided method and data.

    Parameters:
        url (str): The URL to send the request to.
        method (str): The HTTP method to use (e.g., 'GET', 'POST').
        data (dict, optional): The data to send with the request.
        client (httpx.Client, optional): An existing HTTP client to use. If not provided, a new client will be created.
        **kwargs: Additional keyword arguments to pass to the request.

    Returns:
        httpx.Response: The response from the server.

    Raises:
        httpx.HTTPError: If the request fails.
    """
    client = client or httpx.Client()
    if data:
        kwargs["data"] = data
    try:
        response = client.request(method, url, headers=HEADERS, timeout=30, **kwargs)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
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
    """
    Sends an asynchronous HTTP request to the specified URL using the provided method and data.

    Parameters:
        url (str): The URL to send the request to.
        method (str): The HTTP method to use (e.g., 'GET', 'POST').
        data (dict, optional): The data to send with the request.
        client (httpx.AsyncClient, optional): An existing asynchronous HTTP client to use. If not provided, a new client will be created.
        **kwargs: Additional keyword arguments to pass to the request.

    Returns:
        httpx.Response: The response from the server.

    Raises:
        httpx.HTTPError: If the request fails.
    """
    client = client or httpx.AsyncClient()
    if data:
        kwargs["data"] = data
    try:
        response = await client.request(
            method, url, headers=HEADERS, timeout=30, **kwargs
        )
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
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
