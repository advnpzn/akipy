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
