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

# Akinator API wrapper for interacting with the Akinator game.
# This module provides a class `Akinator` that allows users to play the Akinator game programmatically.
import html
import re

try:
    import httpx
except ImportError:
    raise ImportError("httpx must be installed")

from .dicts import THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError, CantGoBackAnyFurther, InvalidChoiceError
from .utils import get_answer_id, request_handler

# Pre-compile regex patterns for performance
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
    The ``Akinator`` class represents the Akinator game.
    You need to create an instance of this class to get started.

    Attributes:
        flag_photo (str): Flag photo URL.
        photo (str): Character photo URL.
        pseudo (str): Pseudo name.
        uri (str): Base URI for API requests.
        theme (str): Theme ID.
        session (str): Session ID.
        signature (str): Signature for API requests.
        identifiant (str): Identifiant for API requests.
        child_mode (bool): Whether child mode is enabled.
        lang (str): Language code.
        available_themes (list): List of available themes.
        question (str): Current question.
        progression (str): Progression percentage.
        step (str): Current step.
        akitude (str): Akitude image name.
        step_last_proposition (str): Last step proposition.
        finished (bool): Whether the game is finished.
        win (bool): Whether the game is won.
        id_proposition (str): ID of the proposed character.
        name_proposition (str): Name of the proposed character.
        description_proposition (str): Description of the proposed character.
        proposition_message (str): Proposition message.
        completion (str): Completion status.
    """

    # Class-level cache for validated languages to avoid redundant network requests
    _validated_languages = set()

    def __init__(self):
        """
        Initializes a new instance of the Akinator class.
        """
        self.flag_photo = None
        self.photo = None
        self.pseudo = None
        self.uri = None
        self.theme = None
        self.session = None
        self.signature = None
        self.identifiant = None
        self.child_mode: bool = False
        self._child_mode_str = "false"  # Cached string representation
        self.lang = None
        self.available_themes = None
        self.theme = None
        self.client = None

        self.question = None
        self.progression = None
        self.step = None
        self.akitude = None
        self.step_last_proposition = ""
        self.finished = False

        self.win = False
        self.id_proposition = None
        self.name_proposition = None
        self.description_proposition = None
        self.proposition_message = ""
        self.completion = None

    def __initialise(self):
        """
        Initializes the Akinator game session by making an API request to get the initial question and session data.

        Raises:
            httpx.HTTPStatusError: If the request to the Akinator server fails.
            ValueError: If the response does not contain expected data.
        """
        url = f"{self.uri}/game"
        data = {"sid": self.theme, "cm": self._child_mode_str}
        if self.client is None:
            self.client = httpx.Client()
        try:
            req = request_handler(url=url, method="POST", data=data, client=self.client)
            req.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            text = req.text

            # Extract session, signature, and identifiant using pre-compiled regex patterns
            self.session = _SESSION_PATTERN.search(text)
            self.signature = _SIGNATURE_PATTERN.search(text)
            self.identifiant = _IDENTIFIANT_PATTERN.search(text)

            if not self.session or not self.signature or not self.identifiant:
                raise ValueError(
                    "Response does not contain expected data: session, signature, or identifiant"
                )

            self.session = self.session.group(1)
            self.signature = self.signature.group(1)
            self.identifiant = self.identifiant.group(1)

            # Extract the initial question
            question_match = _QUESTION_PATTERN.search(text)
            if not question_match:
                raise ValueError("Response does not contain expected data: question")

            self.question = html.unescape(question_match.group(1))

            # Extract the proposition message
            proposition_match = _PROPOSITION_PATTERN.search(text)
            if not proposition_match:
                raise ValueError(
                    "Response does not contain expected data: proposition message"
                )

            self.proposition_message = html.unescape(proposition_match.group(1))

            # Initialize other attributes
            self.progression = "0.00000"
            self.step = "0"
            self.akitude = "defi.png"
        except httpx.HTTPError as e:
            raise httpx.HTTPStatusError(f"Failed to connect to Akinator server: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid response data: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

    def __update(self, action: str, resp: dict):
        """
        Updates the game state based on the response from the API.

        Parameters:
            action (str): The type of action to update ('answer' or 'win').
            resp (dict): The response dictionary from the API.

        Raises:
            NotImplementedError: If the action is not recognized.
        """
        if action == "answer":
            self.akitude = resp["akitude"]
            self.step = resp["step"]
            self.progression = resp["progression"]
            self.question = resp["question"]
        elif action == "win":
            self.win = True
            self.id_proposition = resp["id_proposition"]
            self.name_proposition = resp["name_proposition"]
            self.description_proposition = resp["description_proposition"]
            # This is necessary to prevent Akinator from immediately proposing a new character after an exclusion
            self.step_last_proposition = self.step
            self.pseudo = resp["pseudo"]
            self.flag_photo = resp["flag_photo"]
            self.photo = resp["photo"]
        else:
            raise NotImplementedError(f"Unable to handle action: {action}")

    def __get_region(self, lang):
        """
        Determines the region and theme for the Akinator game based on the provided language.

        Parameters:
            lang (str): The language code or full name of the language.

        Raises:
            InvalidLanguageError: If the provided language is not valid.
            HTTPStatusError: If the request to the Akinator server fails.
        """
        # Map the language code to the full name if necessary
        if len(lang) > 2:
            lang = LANG_MAP.get(lang, lang)
        else:
            # Ensure the provided language is valid
            if lang not in LANG_MAP.values():
                raise InvalidLanguageError(lang)

        # Construct the URL for the Akinator server
        url = f"https://{lang}.akinator.com"

        # Check cache first to avoid redundant validation requests
        if lang not in self._validated_languages:
            # Make a GET request to the Akinator server
            req = request_handler(url=url, method="GET")
            # Check if the request was successful
            if req.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Failed to connect to Akinator server: {req.status_code}"
                )
            # Cache the validated language
            self._validated_languages.add(lang)

        # Update the instance variables with the response data
        self.uri = url
        self.lang = lang

        self.available_themes = THEMES.get(lang, [])
        self.theme = THEME_ID.get(self.available_themes[0], None)

    def start_game(self, language: str | None = "en", child_mode: bool = False):
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
        self.__get_region(lang=language)
        self.__initialise()
        return self

    def handle_response(self, resp: httpx.Response):
        resp.raise_for_status()

        # Check if response is HTML instead of JSON
        content_type = resp.headers.get("content-type", "").lower()
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

    def answer(self, option: str | int):
        if self.win:
            # In proposition mode, we are only supposed to call the /choice or /exclude endpoints. We allow this function to be called with 'yes' or 'no' for convenience, as the website typically displays buttons for these options
            answer = get_answer_id(option)
            if answer == 0:
                return self.choose()
            if answer == 1:
                return self.exclude()
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

        resp = request_handler(url=url, method="POST", data=data, client=self.client)
        self.handle_response(resp)
        return self

    def back(self):
        if self.step == 1:
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

        resp = request_handler(url=url, method="POST", data=data, client=self.client)
        self.handle_response(resp)
        return self

    def exclude(self):
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
            resp = request_handler(
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

    def choose(self):
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

        resp = request_handler(
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

    def defeat(self):
        # The Akinator website normally displays the defeat screen directly using HTML; we replicate here what the user would see
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

    @property
    def confidence(self):
        return float(self.progression) / 100

    @property
    def akitude_url(self):
        return f"{self.uri}/assets/img/akitudes_670x1096/{self.akitude}"

    def yes(self):
        return self.answer("yes")

    def no(self):
        return self.answer("no")

    def close(self):
        """Close the HTTP client if it exists."""
        if self.client is not None:
            self.client.close()
            self.client = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures client is closed."""
        self.close()
        return False

    def __del__(self):
        """Destructor to ensure client is closed."""
        self.close()

    def __str__(self):
        if self.win and not self.finished:
            return f"{self.proposition_message} {self.name_proposition} ({self.description_proposition})"
        return self.question

    def __repr__(self):
        return f"<Akinator: {str(self)}>"
