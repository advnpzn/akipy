import httpx

from .dicts import ANSWER_MAP, HEADERS
from .exceptions import InvalidChoiceError


def request_handler(url: str, method: str, data: dict | None = None, client: httpx.Client | None = None, **kwargs) -> httpx.Response:
    client = client or httpx.Client()
    if data:
        kwargs["data"] = data
    return client.request(method, url, headers=HEADERS, timeout=30, **kwargs)


async def async_request_handler(url: str, method: str, data: dict | None = None, client: httpx.AsyncClient | None = None, **kwargs) -> httpx.Response:
    client = client or httpx.AsyncClient()
    if data:
        kwargs["data"] = data
    return await client.request(method, url, headers=HEADERS, timeout=30, **kwargs)


def get_answer_id(ans: str | int):
    if isinstance(ans, int):
        if ans not in range(5):
            raise InvalidChoiceError(f"Answer ID must be between 0 and 4, got {ans}")
        return ans
    ans2 = ANSWER_MAP.get(ans.lower())
    if ans2 is None:
        raise InvalidChoiceError(f"Invalid answer: {ans}")
    return ans2