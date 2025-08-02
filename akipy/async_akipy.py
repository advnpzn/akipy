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

try:
    import httpx
except ImportError:
    raise ImportError("httpx must be installed")

from .dicts import THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError, CantGoBackAnyFurther, InvalidChoiceError
from .utils import get_answer_id, async_request_handler
from .akinator import (
    Akinator as SyncAkinator,
    SESSION_REGEX,
    SIGNATURE_REGEX,
    IDENTIFIANT_REGEX,
    QUESTION_REGEX,
    PROPOSITION_REGEX,
    WIN_MESSAGE_REGEX,
    ALREADY_PLAYED_REGEX,
    TIMES_SELECTED_REGEX,
    TIMES_REGEX,
)


class Akinator(SyncAkinator):
    """
    The ``Akinator`` Class represents the Akinator Game.
    This is the Asynchronous version, requiring `await` for requests.
    You need to create an Instance of this Class to get started.
    """

    def __del__(self):
        """
        Cleanup resources when the object is destroyed.
        """
        import asyncio

        # Only attempt async cleanup if we have an event loop running
        try:
            loop = asyncio.get_running_loop()
            if loop and not loop.is_closed():
                loop.create_task(self.aclose())
        except RuntimeError:
            # No event loop running, fall back to sync cleanup
            if hasattr(self, "client") and self.client is not None:
                # We can't properly close an async client from sync context
                # but we can at least clear the reference
                self.client = None

    async def aclose(self):
        """
        Close the async HTTP client if it exists.
        """
        if (
            hasattr(self, "client")
            and self.client is not None
            and hasattr(self.client, "aclose")
        ):
            await self.client.aclose()
        self.client = None

    async def __aenter__(self):
        """
        Async context manager entry.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.
        """
        await self.aclose()

    async def __initialise(self):
        url = f"{self.uri}/game"
        data = {"sid": self.theme, "cm": str(self.child_mode).lower()}
        self.client = httpx.AsyncClient()
        try:
            req = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
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

    async def __get_region(self, lang):
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
            req = await async_request_handler(url=url, method="GET")
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
            resp = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
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
            resp = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except Exception as e:
            raise e
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
            "cm": str(self.child_mode).lower(),
            "session": self.session,
            "signature": self.signature,
        }
        self.win = False
        self.id_proposition = ""

        try:
            resp = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except Exception as e:
            raise e
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

        try:
            resp = await async_request_handler(
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
