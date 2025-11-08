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

# Pre-compile regex patterns for performance (shared with sync version)
_SESSION_PATTERN = re.compile(r"#session'\).val\('(.+?)'\)")
_SIGNATURE_PATTERN = re.compile(r"#signature'\).val\('(.+?)'\)")
_IDENTIFIANT_PATTERN = re.compile(r"#identifiant'\).val\('(.+?)'\)")
_QUESTION_PATTERN = re.compile(
    r'<div class="bubble-body"><p class="question-text" id="question-label">(.+)</p></div>'
)
_PROPOSITION_PATTERN = re.compile(
    r'<div class="sub-bubble-propose"><p id="p-sub-bubble">([\w\s]+)</p></div>'
)
_WIN_MESSAGE_PATTERN = re.compile(r'<span class="win-sentence">(.+?)<\/span>')
_ALREADY_PLAYED_PATTERN = re.compile(r'let tokenDejaJoue = "([\w\s]+)";')
_TIMES_SELECTED_PATTERN = re.compile(r'let timesSelected = "(\d+)";')
_TIMES_PATTERN = re.compile(r'<span id="timesselected"><\/span>\s+([\w\s]+)<\/span>')


class Akinator:
    """
    The ``Akinator`` Class represents the Akinator Game.
    This is the Asynchronous version, requiring `await` for requests.
    You need to create an Instance of this Class to get started.
    """

    # Class-level cache for validated languages to avoid redundant network requests
    _validated_languages = set()

    def __init__(self):
        """
        Initializes a new instance of the async Akinator class.
        """
        self.flag_photo = None
        self.photo = None
        self.pseudo = None
        self.uri = None
        self.theme = None
        self.session = None
        self.signature = None
        self.identifiant = None
        self.child_mode = False
        self._child_mode_str = "false"
        self.lang = None
        self.available_themes = []
        self.question = None
        self.progression = None
        self.step = None
        self.akitude = None
        self.step_last_proposition = ""
        self.finished = False
        self.win = False
        self.id_proposition = ""
        self.name_proposition = ""
        self.description_proposition = ""
        self.proposition_message = ""
        self.completion = "OK"
        self.client = None

    async def __initialise(self):
        url = f"{self.uri}/game"
        data = {"sid": self.theme, "cm": self._child_mode_str}
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        try:
            req = (
                await async_request_handler(
                    url=url, method="POST", data=data, client=self.client
                )
            ).text

            self.session = _SESSION_PATTERN.search(req).group(1)
            self.signature = _SIGNATURE_PATTERN.search(req).group(1)
            self.identifiant = _IDENTIFIANT_PATTERN.search(req).group(1)

            match = _QUESTION_PATTERN.search(req)
            self.question = html.unescape(match.group(1))
            self.proposition_message = html.unescape(
                _PROPOSITION_PATTERN.search(req).group(1)
            )
            self.progression = "0.00000"
            self.step = "0"
            self.akitude = "defi.png"
        except Exception:
            raise httpx.HTTPStatusError

    async def __get_region(self, lang):
        # Map the language code to the full name if necessary
        if len(lang) > 2:
            lang = LANG_MAP.get(lang, lang)
        else:
            if lang not in LANG_MAP.values():
                raise InvalidLanguageError(lang)

        url = f"https://{lang}.akinator.com"

        # Check cache first to avoid redundant validation requests
        if lang not in self._validated_languages:
            req = await async_request_handler(url=url, method="GET")
            if req.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Failed to connect to Akinator server: {req.status_code}"
                )
            # Cache the validated language
            self._validated_languages.add(lang)

        self.uri = url
        self.lang = lang

        self.available_themes = THEMES.get(lang, [])
        self.theme = THEME_ID.get(self.available_themes[0], None)

    def __update(self, action: str, resp: dict):
        """Update the instance attributes based on the API response."""
        if action == "answer":
            self.question = html.unescape(resp.get("question", ""))
            self.progression = resp.get("progression", "0.00000")
            self.step = resp.get("step", "0")
            self.akitude = resp.get("akitude", "defi.png")
            self.step_last_proposition = resp.get("step_last_proposition", "")
        elif action == "win":
            self.win = True
            self.id_proposition = resp.get("id_proposition", "")
            self.name_proposition = html.unescape(resp.get("name_proposition", ""))
            self.description_proposition = html.unescape(
                resp.get("description_proposition", "")
            )
            self.pseudo = resp.get("pseudo", "")
            self.photo = resp.get("photo", "")
            self.flag_photo = resp.get("flag_photo", "")
            self.progression = resp.get("progression", "100.00000")
            self.step = resp.get("step", "0")
            self.akitude = resp.get("akitude", "inspiration_legere.png")

    def handle_response(self, resp: httpx.Response):
        """Handle API response and update game state."""
        resp.raise_for_status()

        # Check if response is HTML instead of JSON
        content_type = getattr(resp, "headers", {}).get("content-type", "").lower()
        if "text/html" in content_type:
            text = resp.text
            # The API sometimes returns HTML error pages with 200 status
            if "<!DOCTYPE html>" in text or "<html" in text:
                raise RuntimeError(
                    f"Server returned HTML instead of JSON. This typically means the session has expired "
                    f"or there was a server error. Response preview: {text[:500]}"
                )

        try:
            data = resp.json()
        except Exception as e:
            text = resp.text
            if "A technical problem has occurred." in text:
                raise RuntimeError(
                    f"A technical problem has occurred. Response: {text[:500]}"
                )
            raise RuntimeError(
                f"Failed to parse JSON response. Error: {e}. Response (first 500 chars): {text[:500]}"
            )

        # Handle empty array response from /exclude endpoint when no more characters are available
        if isinstance(data, list) and len(data) == 0:
            raise RuntimeError("No more characters available to propose")

        # Ensure we have a dict to work with
        if not isinstance(data, dict):
            raise RuntimeError(
                f"Unexpected response type: {type(data).__name__}. Response: {data}"
            )

        if "completion" not in data:
            # Assume the completion key is missing because a step has been undone or skipped
            data["completion"] = self.completion
        if data["completion"] == "KO - TIMEOUT":
            raise TimeoutError("The session has timed out.")
        if data["completion"] == "SOUNDLIKE":
            self.finished = True
            self.win = True
            if not self.id_proposition:
                self.defeat()
        elif "id_proposition" in data:
            self.__update(action="win", resp=data)
        else:
            self.__update(action="answer", resp=data)
        self.completion = data["completion"]

    def defeat(self):
        """Handle defeat state when Akinator can't guess the character."""
        self.finished = True
        self.win = False
        self.akitude = "deception.png"
        self.id_proposition = ""
        # TODO: Get the correct defeat message in the user's language
        self.question = (
            "Bravo, you have defeated me !\nShare your feat with your friends"
        )
        self.progression = "100.00000"
        return self

    async def start_game(self, language: str | None = "en", child_mode: bool = False):
        """
        This method is responsible for actually starting the game scene.
        You can pass the following parameters to set your language preference and as well as the Child Mode.
        If language is not set, English is used by default. Child Mode is set to ``False`` by default.
        :param language: "en"
        :param child_mode: False
        :return: The first question asked by the Akinator.
        """
        self.child_mode = child_mode
        self._child_mode_str = str(child_mode).lower()
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
            raise InvalidChoiceError(
                "Only 'yes' or 'no' can be answered when Akinator has proposed a win"
            )
        url = f"{self.uri}/answer"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": self._child_mode_str,
            "answer": get_answer_id(option),
            "step_last_proposition": self.step_last_proposition,
            "session": self.session,
            "signature": self.signature,
        }

        resp = await async_request_handler(
            url=url, method="POST", data=data, client=self.client
        )
        self.handle_response(resp)
        return self

    async def back(self):
        if int(self.step) <= 1:
            raise CantGoBackAnyFurther("You are already at the first question")
        url = f"{self.uri}/cancel_answer"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": self._child_mode_str,
            "session": self.session,
            "signature": self.signature,
        }
        self.win = False

        resp = await async_request_handler(
            url=url, method="POST", data=data, client=self.client
        )
        self.handle_response(resp)
        return self

    async def exclude(self):
        if not self.win:
            raise InvalidChoiceError(
                "You can only exclude when Akinator has proposed a win"
            )
        if self.finished:
            return self.defeat()
        url = f"{self.uri}/exclude"
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": self._child_mode_str,
            "session": self.session,
            "signature": self.signature,
            "forward_answer": "0",
        }
        self.win = False
        self.id_proposition = ""

        try:
            resp = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except RuntimeError as e:
            # If the exclude endpoint fails (returns HTML, empty array, or errors),
            # it likely means we've reached the end of the game with no more characters
            # In this case, treat it as a defeat
            error_msg = str(e)
            if any(
                msg in error_msg
                for msg in [
                    "HTML instead of JSON",
                    "Failed to parse JSON",
                    "No more characters available",
                ]
            ):
                return self.defeat()
            # Re-raise other errors
            raise
        return self

    async def choose(self):
        if not self.win:
            raise InvalidChoiceError(
                "You can only choose when Akinator has proposed a win"
            )
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

        resp = await async_request_handler(
            url=url,
            method="POST",
            data=data,
            client=self.client,
            follow_redirects=True,
        )
        if resp.status_code not in range(200, 400):
            resp.raise_for_status()
        self.finished = True
        self.win = True
        self.akitude = "triomphe.png"
        self.id_proposition = ""
        try:
            text = resp.text
            # The response for this request is always HTML+JS, so we need to parse it to get the number of times the character has been played, and the win message in the correct language
            win_message = html.unescape(_WIN_MESSAGE_PATTERN.search(text).group(1))
            already_played = html.unescape(
                _ALREADY_PLAYED_PATTERN.search(text).group(1)
            )
            times_selected = _TIMES_SELECTED_PATTERN.search(text).group(1)
            times = html.unescape(_TIMES_PATTERN.search(text).group(1))
            self.question = f"{win_message}\n{already_played} {times_selected} {times}"
        except Exception:
            pass
        self.progression = "100.00000"
        return self

    async def close(self):
        """Close the HTTP client if it exists."""
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures client is closed."""
        await self.close()
        return False

    def __del__(self):
        """Warn if client wasn't properly closed."""
        if self.client is not None:
            import warnings

            warnings.warn(
                "Akinator async client was not properly closed. "
                "Use 'async with Akinator()' or call 'await aki.close()' explicitly.",
                ResourceWarning,
                stacklevel=2,
            )

    @property
    def confidence(self):
        """Return the confidence level as a float between 0 and 1."""
        return float(self.progression) / 100

    @property
    def akitude_url(self):
        """Return the full URL to the akitude image."""
        return f"{self.uri}/assets/img/akitudes_670x1096/{self.akitude}"

    async def yes(self):
        """Convenience method to answer 'yes'."""
        return await self.answer("yes")

    async def no(self):
        """Convenience method to answer 'no'."""
        return await self.answer("no")

    def __str__(self):
        """Return a string representation of the current question or result."""
        if self.win and not self.finished:
            return f"{self.proposition_message} {self.name_proposition} ({self.description_proposition})"
        return self.question or ""

    def __repr__(self):
        """Return a detailed string representation of the Akinator instance."""
        return f"Akinator(question={self.question!r}, step={self.step}, progression={self.progression})"
