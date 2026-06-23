import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
]

ACCEPT_VALUES = [
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
]

ACCEPT_LANGUAGE_VALUES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-US,en;q=0.5",
    "en,en;q=0.9",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest",
}


def generate_headers() -> dict:
    return {
        "Accept": random.choice(ACCEPT_VALUES),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": random.choice(ACCEPT_LANGUAGE_VALUES),
        "User-Agent": random.choice(USER_AGENTS),
        "x-requested-with": "XMLHttpRequest",
    }


LANG_MAP = {
    "english": "en",
    "arabic": "ar",
    "chinese": "cn",
    "german": "de",
    "spanish": "es",
    "french": "fr",
    "hebrew": "il",
    "italian": "it",
    "japanese": "jp",
    "korean": "kr",
    "dutch": "nl",
    "polish": "pl",
    "portuguese": "pt",
    "russian": "ru",
    "turkish": "tr",
    "indonesian": "id",
}

THEME_ID = {"c": 1, "a": 14, "o": 2}

"""
c - characters
a - animals
o - objects
"""

THEMES = {
    "en": ["c", "a", "o"],
    "ar": ["c"],
    "cn": ["c"],
    "de": ["c", "a"],
    "es": ["c", "a"],
    "fr": ["c", "a", "o"],
    "il": ["c"],
    "it": ["c", "a"],
    "jp": ["c", "a"],
    "kr": ["c"],
    "nl": ["c"],
    "pl": ["c"],
    "pt": ["c"],
    "ru": ["c"],
    "tr": ["c"],
    "id": ["c"],
}

ANSWERS = {
    0: ["yes", "y", "0"],
    1: ["no", "n", "1"],
    2: ["i", "idk", "i dont know", "i don't know", "2"],
    3: ["p", "probably", "3"],
    4: ["pn", "probably not", "4"],
}
ANSWER_MAP = {a: key for key, values in ANSWERS.items() for a in values}
