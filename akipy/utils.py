import httpx

from .dicts import ANSWERS, HEADERS


def request_handler(url: str, method: str, data: dict | None = None) -> httpx.Response:
    if method == 'GET':
        return httpx.get(url, headers=HEADERS, timeout=30.0)
    elif method == 'POST':
        return httpx.post(url, headers=HEADERS, data=data, timeout=30.0)


def get_answer_id(ans: str | int):
    for key, values in ANSWERS.items():
        if ans in values:
            return key
        else:
            continue
