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
import html
import re

try:
    import httpx
except ImportError:
    raise ImportError("httpx must be installed")

from .dicts import THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError, CantGoBackAnyFurther, InvalidChoiceError
from .utils import get_answer_id, async_request_handler
from .akinator import Akinator as SyncAkinator


class Akinator(SyncAkinator):
    """
    The ``Akinator`` Class represents the Akinator Game.
    This is the Asynchronous version, requiring `await` for requests.
    You need to create an Instance of this Class to get started.
    """

    async def __initialise(self):
        url = f"{self.uri}/game"
        data = {
            "sid": self.theme,
            "cm": str(self.child_mode).lower()
        }
        self.client = httpx.AsyncClient()
        try:
            req = (await async_request_handler(url=url, method="POST", data=data, client=self.client)).text
            
            self.session = re.search(r"#session'\).val\('(.+?)'\)", req).group(1)
            self.signature = re.search(r"#signature'\).val\('(.+?)'\)", req).group(1)
            self.identifiant = re.search(r"#identifiant'\).val\('(.+?)'\)", req).group(1)

            match = re.search(
                r'<div class="bubble-body"><p class="question-text" id="question-label">(.+)</p></div>',
                req,
            )
            self.question = html.unescape(match.group(1))
            self.proposition_message = html.unescape(re.search(
                r'<div class="sub-bubble-propose"><p id="p-sub-bubble">([\w\s]+)</p></div>',
                req,
            ).group(1))
            self.progression = "0.00000"
            self.step = "0"
            self.akitude = 'defi.png'
        except Exception:
            raise httpx.HTTPStatusError

    async def __get_region(self, lang):
        try:
            if len(lang) > 2:
                lang = LANG_MAP[lang]
            else:
                assert (lang in LANG_MAP.values())
        except Exception:
            raise InvalidLanguageError(lang)
        url = f"https://{lang}.akinator.com"
        try:
            req = await async_request_handler(url=url, method='GET')
            if req.status_code != 200:
                raise httpx.HTTPStatusError
            else:
                self.uri = url
                self.lang = lang

                self.available_themes = THEMES[lang]
                self.theme = THEME_ID[self.available_themes[0]]
        except Exception as e:
            raise e

    async def start_game(self, language: str | None = "en", child_mode: bool = False):
        """
        This method is responsible for actually starting the game scene.
        You can pass the following parameters to set your language preference and as well as the Child Mode.
        If language is not set, English is used by default. Child Mode is set to ``False`` by default.
        :param language: "en"
        :param child_mode: False
        :return: The first question asked by the Akinator.
        """

        await self.__get_region(language)
        await self.__initialise()
        return self

    async def answer(self, option: str | int):
        if self.win:
            # In proposition mode, we are only supposed to call the /choice or /exclude endpoints. We allow this function to be called with 'yes' or 'no' for convenience, as the website typically displays buttons for these options
            answer = get_answer_id(option)
            if answer == 0:
                return await self.choose()
            if answer == 1:
                return await self.exclude()
            raise InvalidChoiceError("Only 'yes' or 'no' can be answered when Akinator has proposed a win")
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
            resp = await async_request_handler(url=url, method='POST', data=data, client=self.client)
            self.handle_response(resp)
        except Exception as e:
            raise e
        return self

    async def back(self):
        if self.step == 1:
            raise CantGoBackAnyFurther("You are already at the first question")
        url = f"{self.uri}/cancel_answer"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": str(self.child_mode).lower(),
            "session": self.session,
            "signature": self.signature,
        }
        self.win = False

        try:
            resp = await async_request_handler(url=url, method='POST', data=data, client=self.client)
            self.handle_response(resp)
        except Exception as e:
            raise e
        return self

    async def exclude(self):
        if not self.win:
            raise InvalidChoiceError("You can only exclude when Akinator has proposed a win")
        if self.finished:
            return self.defeat()
        url = f"{self.uri}/exclude"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": str(self.child_mode).lower(),
            "session": self.session,
            "signature": self.signature,
        }
        self.win = False
        self.id_proposition = ""

        try:
            resp = await async_request_handler(url=url, method='POST', data=data, client=self.client)
            self.handle_response(resp)
        except Exception as e:
            raise e
        return self

    async def choose(self):
        if not self.win:
            raise InvalidChoiceError("You can only choose when Akinator has proposed a win")
        url = f"{self.uri}/choice"
        data = {
            "step": self.step,
            "sid": self.theme,
            "session": self.session,
            "signature": self.signature,
            "identifiant": self.identifiant,
            "pid": self.id_proposition,
            "charac_name": self.name_proposition,
            "charac_desc": self.description_proposition,
            "pflag_photo": self.flag_photo,
        }

        try:
            resp = await async_request_handler(url=url, method='POST', data=data, client=self.client, follow_redirects=True)
            if resp.status_code not in range(200, 400):
                resp.raise_for_status()
        except Exception as e:
            raise e
        self.finished = True
        self.win = True
        self.akitude = 'triomphe.png'
        self.id_proposition = ""
        try:
            text = resp.text
            # The response for this request is always HTML+JS, so we need to parse it to get the number of times the character has been played, and the win message in the correct language
            win_message = html.unescape(re.search(r'<span class="win-sentence">(.+?)<\/span>', text).group(1))
            already_played = html.unescape(re.search(r'let tokenDejaJoue = "([\w\s]+)";', text).group(1))
            times_selected = re.search(r'let timesSelected = "(\d+)";', text).group(1)
            times = html.unescape(re.search(r'<span id="timesselected"><\/span>\s+([\w\s]+)<\/span>', text).group(1))
            self.question = f"{win_message}\n{already_played} {times_selected} {times}"
        except Exception:
            pass
        self.progression = '100.00000'
        return self