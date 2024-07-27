"""
MIT License

Copyright (c) 2024 advnpzn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import json
import re
import httpx

from .dicts import HEADERS, THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError, CantGoBackAnyFurther
from .utils import get_answer_id, request_handler


class Akinator:
    """
    The Akinator Class represents the Akinator Game.
    You need to create an instance of this class to get started.
    """

    def __init__(self):
        self.photo = None
        self.pseudo = None
        self.uri = None
        self.theme = None
        self.session = None
        self.signature = None
        self.child_mode = False
        self.lang = None
        self.available_themes = None
        self.theme = None

        self.question = None
        self.progression = None
        self.step = None
        self.akitude = None
        self.step_last_proposition = ""

        self.win = False
        self.name_proposition = None
        self.description_proposition = None
        self.completion = None

    def start_game(self, language: str = "en", child_mode: bool = False):
        """
        Start the Akinator game with specified language and child mode.
        :param language: Language code or name
        :param child_mode: Whether to enable child mode
        :return: None
        """
        self.__get_region(lang=language)
        self.__initialise()

    def answer(self, option):
        url = f"{self.uri}/answer"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": str(self.child_mode).lower(),
            "answer": get_answer_id(option),
            "step_last_proposition": self.step_last_proposition,
            "session": self.session,
            "signature": self.signature,
        }

        try:
            req = request_handler(url=url, method='POST', data=data)
            resp = req.json()

            if "id_proposition" in resp:
                self.__update(action="win", resp=resp)
            else:
                self.__update(action="answer", resp=resp)
            self.completion = resp.get('completion')
        except Exception as e:
            raise e

    def back(self):
        if self.step == 1:
            raise CantGoBackAnyFurther("Cannot go back further.")
        else:
            url = f"{self.uri}/cancel_answer"
            data = {
                "step": self.step,
                "progression": self.progression,
                "sid": self.theme,
                "cm": str(self.child_mode).lower(),
                "session": self.session,
                "signature": self.signature,
            }

            try:
                req = request_handler(url=url, method='POST', data=data)
                resp = req.json()
                self.__update(action="back", resp=resp)
            except Exception as e:
                raise e

    def __update(self, action: str, resp):
        if action in ["answer", "back"]:
            self.akitude = resp.get('akitude')
            self.step = resp.get('step')
            self.progression = resp.get('progression')
            self.question = resp.get('question')
        elif action == "win":
            self.win = True
            self.name_proposition = resp.get('name_proposition')
            self.description_proposition = resp.get('description_proposition')
            self.pseudo = resp.get('pseudo')
            self.photo = resp.get('photo')

    def __get_region(self, lang):
        try:
            lang = LANG_MAP.get(lang, lang)  # Get mapped language if available
            if len(lang) > 2 and lang not in LANG_MAP.values():
                raise InvalidLanguageError(lang)
        except Exception:
            raise InvalidLanguageError(lang)

        url = f"https://{lang}.akinator.com"
        try:
            req = request_handler(url=url, method='GET')
            if req.status_code != 200:
                raise httpx.HTTPStatusError(f"HTTP status error: {req.status_code}")
            self.uri = url
            self.lang = lang
            self.available_themes = THEMES.get(lang, [])
            self.theme = THEME_ID.get(self.available_themes[0])
        except Exception as e:
            raise e

    def __initialise(self):
        url = f"{self.uri}/game"
        data = {
            "sid": self.theme,
            "cm": str(self.child_mode).lower()
        }
        try:
            req = request_handler(url=url, method='POST', data=data).text
            match = re.findall(r"[a-zA-Z0-9+/]+==", req)

            if len(match) >= 2:
                self.session = match[0]
                self.signature = match[1]

            match = re.search(r'<div class="bubble-body"><p class="question-text" id="question-label">(.*?)</p></div>', req)
            self.question = match.group(1) if match else None
            self.progression = "0.00000"
            self.step = 0
        except Exception as e:
            raise httpx.HTTPStatusError(f"Failed to initialise: {e}")
