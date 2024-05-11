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

try:
    import httpx
except ImportError:
    raise ImportError('httpx is not installed')

from .dicts import HEADERS, THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError, CantGoBackAnyFurther
from .utils import get_answer_id, request_handler


class Akinator:
    """
    The ``Akinator`` Class represents the Akinator Game.
    You need to create an Instance of this Class to get started.
    """

    def __init__(self):
        self.photo = None
        self.pseudo = None
        self.uri = None
        self.theme = None
        self.session = None
        self.signature = None
        self.child_mode: bool = False
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

    def start_game(self, language: str | None = "en", child_mode: bool = False):
        """
        This method is responsible for actually starting the game scene.
        You can pass the following parameters to set your language preference and as well as the Child Mode.
        If language is not set, English is used by default. Child Mode is set to ``False`` by default.
        :param language: "en"
        :param child_mode: False
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
            resp = json.loads(req.text)

            if re.findall(r"id_proposition", str(resp)):
                self.__update(action="win", resp=resp)
            else:
                self.__update(action="answer", resp=resp)
            self.completion = resp['completion']
        except Exception as e:
            raise e

    def back(self):
        if self.step == 1:
            raise CantGoBackAnyFurther
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
                resp = json.loads(req.text)
                self.__update(action="back", resp=resp)
            except Exception as e:
                raise e

    def __update(self, action: str, resp):
        if action == "answer":
            self.akitude = resp['akitude']
            self.step = resp['step']
            self.progression = resp['progression']
            self.question = resp['question']
        elif action == "back":
            self.akitude = resp['akitude']
            self.step = resp['step']
            self.progression = resp['progression']
            self.question = resp['question']
        elif action == "win":
            self.win = True
            self.name_proposition = resp['name_proposition']
            self.description_proposition = resp['description_proposition']
            self.pseudo = resp['pseudo']
            self.photo = resp['photo']

    def __get_region(self, lang):
        try:
            if len(lang) > 2:
                lang = LANG_MAP[lang]
            else:
                assert (lang in LANG_MAP.values())
        except Exception:
            raise InvalidLanguageError(lang)
        url = f"https://{lang}.akinator.com"
        try:
            req = request_handler(url=url, method='GET')
            if req.status_code != 200:
                raise httpx.HTTPStatusError
            else:
                self.uri = url
                self.lang = lang

                self.available_themes = THEMES[lang]
                self.theme = THEME_ID[self.available_themes[0]]
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
            match = re.findall(r"[a-zA-Z0-9+/]+==", req)[-2:]

            self.session = match[0]
            self.signature = match[1]

            match = re.search(r'<div class="bubble-body"><p class="question-text" id="question-label">(.*?)</p></div>',
                              req)
            self.question = match.group(1)
            self.progression = "0.00000"
            self.step = 0
        except Exception:
            raise httpx.HTTPStatusError
