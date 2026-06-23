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
import warnings

try:
    import httpx
except ImportError:
    raise ImportError("httpx must be installed")

from ._base import (
    _BaseAkinator,
    WIN_MESSAGE_PATTERN,
    ALREADY_PLAYED_PATTERN,
    TIMES_SELECTED_PATTERN,
    TIMES_PATTERN,
)
from .exceptions import CantGoBackAnyFurther, InvalidChoiceError
from .utils import get_answer_id, async_request_handler


class Akinator(_BaseAkinator):
    """
    The ``Akinator`` Class represents the Akinator Game.
    This is the Asynchronous version, requiring ``await`` for requests.
    You need to create an Instance of this Class to get started.
    """

    def __init__(self):
        super().__init__()

    async def __initialise(self):
        url = f"{self.uri}/game"
        data = {"sid": self.theme, "cm": self._child_mode_str}
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        try:
            req = await async_request_handler(
                url=url, method="POST", data=data, client=self.client
            )
            self._parse_init_response(req.text)
        except httpx.HTTPError as e:
            raise httpx.HTTPStatusError(f"Failed to connect to Akinator server: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid response data: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred: {e}")

    async def start_game(self, language: str | None = "en", child_mode: bool = False):
        """
        Start the Akinator game. English and non-child mode are used by default.
        :param language: "en"
        :param child_mode: False
        :return: self
        """
        self.child_mode = child_mode
        self._child_mode_str = str(child_mode).lower()
        self._set_region(language)
        await self.__initialise()
        return self

    async def answer(self, option: str | int):
        if self.win:
            answer = get_answer_id(option)
            if answer == 0:
                return await self.choose()
            if answer == 1:
                return await self.exclude()
            raise InvalidChoiceError(
                "Only 'yes' or 'no' can be answered when Akinator has proposed a win"
            )
        data = self._base_data()
        data["answer"] = get_answer_id(option)
        data["step_last_proposition"] = self.step_last_proposition
        resp = await async_request_handler(
            url=f"{self.uri}/answer", method="POST", data=data, client=self.client
        )
        self.handle_response(resp)
        return self

    async def back(self):
        if int(self.step) <= 1:
            raise CantGoBackAnyFurther("You are already at the first question")
        self.win = False
        resp = await async_request_handler(
            url=f"{self.uri}/cancel_answer",
            method="POST",
            data=self._base_data(),
            client=self.client,
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
        data = self._base_data()
        data["forward_answer"] = "0"
        self.win = False
        self.id_proposition = ""
        try:
            resp = await async_request_handler(
                url=f"{self.uri}/exclude", method="POST", data=data, client=self.client
            )
            self.handle_response(resp)
        except RuntimeError as e:
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
            raise
        return self

    async def choose(self):
        if not self.win:
            raise InvalidChoiceError(
                "You can only choose when Akinator has proposed a win"
            )
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
            url=f"{self.uri}/choice",
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
            win_message = html.unescape(WIN_MESSAGE_PATTERN.search(text).group(1))
            already_played = html.unescape(ALREADY_PLAYED_PATTERN.search(text).group(1))
            times_selected = TIMES_SELECTED_PATTERN.search(text).group(1)
            times = html.unescape(TIMES_PATTERN.search(text).group(1))
            self.question = f"{win_message}\n{already_played} {times_selected} {times}"
        except Exception:
            pass
        self.progression = "100.00000"
        return self

    async def yes(self):
        return await self.answer("yes")

    async def no(self):
        return await self.answer("no")

    async def close(self):
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
        return False

    def __del__(self):
        if self.client is not None:
            warnings.warn(
                "Akinator async client was not properly closed. "
                "Use 'async with Akinator()' or call 'await aki.close()' explicitly.",
                ResourceWarning,
                stacklevel=2,
            )
