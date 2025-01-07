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


def html_decode(s) -> str:
	"Decodes HTML encoded characters in a string."
	while len(s) > 7:
		try:
			i = s.index("&#")
		except ValueError:
			break
		try:
			if s[i + 2] == "x":
				base = 16
				p = i + 3
			else:
				base = 10
				p = i + 2
			for a in range(p, p + 16):
				c = s[a]
				if c == ";":
					v = int(s[p:a], base)
					break
				elif not c.isnumeric() and c not in "abcdefABCDEF":
					break
			c = chr(v)
			s = s[:i] + c + s[a + 1:]
		except (ValueError, NameError, IndexError):
			s = s[:i + 1] + "\u200b" + s[i + 1:]
			continue
	s = s.replace("<b>", "**").replace("</b>", "**").replace("<i>", "*").replace("</i>", "*").replace("<u>", "*").replace("</u>", "*")
	s = s.replace("\u200b", "").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
	return s.replace("&quot;", '"').replace("&apos;", "'")