from typing import Union, Optional
import httpx

from .dicts import ANSWERS, HEADERS

def request_handler(url: str, method: str, data: Optional[dict] = None) -> httpx.Response:
    if method == 'GET':
        return httpx.get(url, headers=HEADERS, timeout=30.0)
    elif method == 'POST':
        return httpx.post(url, headers=HEADERS, data=data, timeout=30.0)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

async def async_request_handler(url: str, method: str, data: Optional[dict] = None) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        if method == 'GET':
            return await client.get(url, headers=HEADERS, timeout=30.0)
        elif method == 'POST':
            return await client.post(url, headers=HEADERS, data=data, timeout=30.0)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

def get_answer_id(ans):
    for key, values in ANSWERS.items():
        if ans.lower() in values:
            return key
    return None
