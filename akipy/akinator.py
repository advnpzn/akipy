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

# Pre-compiled regular expressions for better performance
SESSION_REGEX = re.compile(r"#session'\).val\('(.+?)'\)")
SIGNATURE_REGEX = re.compile(r"#signature'\).val\('(.+?)'\)")
IDENTIFIANT_REGEX = re.compile(r"#identifiant'\).val\('(.+?)'\)")
QUESTION_REGEX = re.compile(
    r'<div class="bubble-body"><p class="question-text" id="question-label">(.+)</p></div>'
)
PROPOSITION_REGEX = re.compile(
    r'<div class="sub-bubble-propose"><p id="p-sub-bubble">([\w\s]+)</p></div>'
)
WIN_MESSAGE_REGEX = re.compile(r'<span class="win-sentence">(.+?)</span>')
ALREADY_PLAYED_REGEX = re.compile(r'let tokenDejaJoue = "([\w\s]+)";')
TIMES_SELECTED_REGEX = re.compile(r'let timesSelected = "(\d+)";')
TIMES_REGEX = re.compile(r'<span id="timesselected"></span>\s+([\w\s]+)</span>')


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

    def __del__(self):
        """
        Cleanup resources when the object is destroyed.
        """
        self.close()

    def close(self):
        """
        Close the HTTP client if it exists.
        """
        if (
            hasattr(self, "client")
            and self.client is not None
            and hasattr(self.client, "close")
        ):
            self.client.close()
        self.client = None

    def __initialise(self):
        """
        Initializes the Akinator game session by making an API request to get the initial question and session data.

        Raises:
            httpx.HTTPStatusError: If the request to the Akinator server fails.
            ValueError: If the response does not contain expected data.
        """
        url = f"{self.uri}/game"
        data = {"sid": self.theme, "cm": str(self.child_mode).lower()}
        self.client = httpx.Client()
        try:
            req = request_handler(url=url, method="POST", data=data, client=self.client)
            text = req.text

            # Extract session, signature, and identifiant using pre-compiled regular expressions
            session_match = SESSION_REGEX.search(text)
            signature_match = SIGNATURE_REGEX.search(text)
            identifiant_match = IDENTIFIANT_REGEX.search(text)

            if not session_match or not signature_match or not identifiant_match:
                raise ValueError(
                    "Response does not contain expected data: session, signature, or identifiant"
                )

            self.session = session_match.group(1)
            self.signature = signature_match.group(1)
            self.identifiant = identifiant_match.group(1)

            # Extract the initial question
            question_match = QUESTION_REGEX.search(text)
            if not question_match:
                raise ValueError("Response does not contain expected data: question")

            self.question = html.unescape(question_match.group(1))

            # Extract the proposition message
            proposition_match = PROPOSITION_REGEX.search(text)
            if not proposition_match:
                raise ValueError(
                    "Response does not contain expected data: proposition message"
                )

            self.proposition_message = html.unescape(proposition_match.group(1))

            # Initialize other attributes
            self.progression = "0.00000"
            self.step = "0"
            self.akitude = "defi.png"
        except httpx.HTTPStatusError as e:
            raise httpx.HTTPStatusError(f"Failed to connect to Akinator server: {e}")
        except httpx.RequestError as e:
            raise httpx.RequestError(f"Request failed: {e}")
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
        try:
            # Map the language code to the full name if necessary
            if len(lang) > 2:
                # For language names, check if they exist in LANG_MAP
                if lang not in LANG_MAP:
                    raise InvalidLanguageError(f"Invalid language name: {lang}")
                lang = LANG_MAP[lang]
            else:
                # For language codes, ensure they are valid
                if lang not in LANG_MAP.values():
                    raise InvalidLanguageError(f"Invalid language code: {lang}")
        except InvalidLanguageError:
            raise

        # Construct the URL for the Akinator server
        url = f"https://{lang}.akinator.com"

        try:
            # Make a GET request to the Akinator server
            req = request_handler(url=url, method="GET")
            # Check if the request was successful
            if req.status_code != 200:
                raise httpx.HTTPStatusError(
                    f"Failed to connect to Akinator server: {req.status_code}"
                )
            else:
                # Update the instance variables with the response data
                self.uri = url
                self.lang = lang

                self.available_themes = THEMES.get(lang, [])
                if self.available_themes:
                    self.theme = THEME_ID.get(self.available_themes[0], None)
                else:
                    raise InvalidLanguageError(
                        f"No themes available for language: {lang}"
                    )
        except Exception as e:
            raise e

    def start_game(self, language: str | None = "en", child_mode: bool = False):
        """
        This method is responsible for actually starting the game scene.
        You can pass the following parameters to set your language preference and as well as the Child Mode.
        If language is not set, English is used by default. Child Mode is set to ``False`` by default.
        :param language: "en"
        :param child_mode: False
        :return: The first question asked by the Akinator.
        """

        self.__get_region(lang=language)
        self.__initialise()
        return self

    def handle_response(self, resp: httpx.Response):
        resp.raise_for_status()
        try:
            data = resp.json()
        except Exception:
            text = resp.text
            if "A technical problem has occurred." in text:
                raise RuntimeError("A technical problem has occurred.")
            raise RuntimeError(f"Unexpected response: {text}")
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
            "cm": str(self.child_mode).lower(),
            "answer": get_answer_id(option),
            "step_last_proposition": self.step_last_proposition,
            "session": self.session,
            "signature": self.signature,
        }

        try:
            resp = request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except Exception as e:
            raise e
        return self

    def back(self):
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
            resp = request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except Exception as e:
            raise e
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
            "cm": str(self.child_mode).lower(),
            "session": self.session,
            "signature": self.signature,
        }
        self.win = False
        self.id_proposition = ""

        try:
            resp = request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except Exception as e:
            raise e
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

        try:
            resp = request_handler(
                url=url,
                method="POST",
                data=data,
                client=self.client,
                follow_redirects=True,
            )
            if resp.status_code not in range(200, 400):
                resp.raise_for_status()
        except Exception as e:
            raise e
        self.finished = True
        self.win = True
        self.akitude = "triomphe.png"
        self.id_proposition = ""
        try:
            text = resp.text
            # The response for this request is always HTML+JS, so we need to parse it to get the number of times the character has been played, and the win message in the correct language
            win_message_match = WIN_MESSAGE_REGEX.search(text)
            already_played_match = ALREADY_PLAYED_REGEX.search(text)
            times_selected_match = TIMES_SELECTED_REGEX.search(text)
            times_match = TIMES_REGEX.search(text)

            if (
                win_message_match
                and already_played_match
                and times_selected_match
                and times_match
            ):
                win_message = html.unescape(win_message_match.group(1))
                already_played = html.unescape(already_played_match.group(1))
                times_selected = times_selected_match.group(1)
                times = html.unescape(times_match.group(1))
                self.question = (
                    f"{win_message}\n{already_played} {times_selected} {times}"
                )
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

    def __str__(self):
        if self.win and not self.finished:
            return f"{self.proposition_message} {self.name_proposition} ({self.description_proposition})"
        return self.question

    def __repr__(self):
        return f"<Akinator: {str(self)}>"
