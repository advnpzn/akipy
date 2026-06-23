"""Shared base class and compiled regex patterns for sync and async Akinator."""

import html
import re

import httpx

from .dicts import THEME_ID, THEMES, LANG_MAP
from .exceptions import InvalidLanguageError
from .flaresolverr import FlareSolverrClient, AsyncFlareSolverrClient

# Compiled once at import time, shared by both subclasses
SESSION_PATTERN = re.compile(r"#session'\).val\('(.+?)'\)")
SIGNATURE_PATTERN = re.compile(r"#signature'\).val\('(.+?)'\)")
IDENTIFIANT_PATTERN = re.compile(r"#identifiant'\).val\('(.+?)'\)")
QUESTION_PATTERN = re.compile(
    r'<div class="bubble-body"><p class="question-text" id="question-label">(.+)</p></div>'
)
PROPOSITION_PATTERN = re.compile(
    r'<div class="sub-bubble-propose"><p id="p-sub-bubble">([\w\s]+)</p></div>'
)
WIN_MESSAGE_PATTERN = re.compile(r'<span class="win-sentence">(.+?)<\/span>')
ALREADY_PLAYED_PATTERN = re.compile(r'let tokenDejaJoue = "([\w\s]+)";')
TIMES_SELECTED_PATTERN = re.compile(r'let timesSelected = "(\d+)";')
TIMES_PATTERN = re.compile(r'<span id="timesselected"><\/span>\s+([\w\s]+)<\/span>')


class _BaseAkinator:
    """Shared state and pure-Python logic for sync and async Akinator subclasses."""

    _validated_languages: set = set()

    def __init__(self, flaresolverr_url: str | None = None):
        self.flag_photo = None
        self.photo = None
        self.pseudo = None
        self.uri = None
        self.theme = None
        self.session = None
        self.signature = None
        self.identifiant = None
        self.child_mode: bool = False
        self._child_mode_str: str = "false"
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
        self.flaresolverr_url = flaresolverr_url
        self._flaresolverr_client: (
            FlareSolverrClient | AsyncFlareSolverrClient | None
        ) = None
        self._flaresolverr_cookies: dict = {}
        self._flaresolverr_user_agent: str | None = None

    def _set_region(self, lang: str) -> None:
        """Resolve and validate language purely from local dicts — no network call."""
        if len(lang) > 2:
            lang = LANG_MAP.get(lang, lang)
        else:
            if lang not in LANG_MAP.values():
                raise InvalidLanguageError(lang)
        self.uri = f"https://{lang}.akinator.com"
        self.lang = lang
        self.available_themes = THEMES.get(lang, [])
        self.theme = THEME_ID.get(self.available_themes[0], None)

    def _parse_init_response(self, text: str) -> None:
        """Extract session credentials and first question from the /game HTML response."""
        session_m = SESSION_PATTERN.search(text)
        signature_m = SIGNATURE_PATTERN.search(text)
        identifiant_m = IDENTIFIANT_PATTERN.search(text)
        if not (session_m and signature_m and identifiant_m):
            raise ValueError(
                "Response does not contain expected data: session, signature, or identifiant"
            )
        self.session = session_m.group(1)
        self.signature = signature_m.group(1)
        self.identifiant = identifiant_m.group(1)

        question_m = QUESTION_PATTERN.search(text)
        if not question_m:
            raise ValueError("Response does not contain expected data: question")
        self.question = html.unescape(question_m.group(1))

        proposition_m = PROPOSITION_PATTERN.search(text)
        if not proposition_m:
            raise ValueError(
                "Response does not contain expected data: proposition message"
            )
        self.proposition_message = html.unescape(proposition_m.group(1))

        self.progression = "0.00000"
        self.step = "0"
        self.akitude = "defi.png"

    def _base_data(self) -> dict:
        """Common form fields shared across answer/back/exclude requests."""
        return {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": self._child_mode_str,
            "session": self.session,
            "signature": self.signature,
        }

    def _update(self, action: str, resp: dict) -> None:
        if action == "answer":
            self.akitude = resp.get("akitude", self.akitude)
            self.step = resp.get("step", self.step)
            self.progression = resp.get("progression", self.progression)
            self.question = html.unescape(resp.get("question", ""))
        elif action == "win":
            self.win = True
            self.step_last_proposition = self.step
            self.id_proposition = resp.get("id_proposition", "")
            self.name_proposition = html.unescape(resp.get("name_proposition", ""))
            self.description_proposition = html.unescape(
                resp.get("description_proposition", "")
            )
            self.pseudo = resp.get("pseudo", "")
            self.flag_photo = resp.get("flag_photo", "")
            self.photo = resp.get("photo", "")
            self.progression = resp.get("progression", self.progression)
            self.step = resp.get("step", self.step)
            self.akitude = resp.get("akitude", self.akitude)
        else:
            raise NotImplementedError(f"Unable to handle action: {action}")

    def handle_response(self, resp: httpx.Response) -> None:
        """Parse an API response and update game state. Used by both sync and async paths."""
        resp.raise_for_status()

        content_type = getattr(resp, "headers", {}).get("content-type", "").lower()
        if "text/html" in content_type:
            text = resp.text
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

        if isinstance(data, list) and len(data) == 0:
            raise RuntimeError("No more characters available to propose")
        if not isinstance(data, dict):
            raise RuntimeError(
                f"Unexpected response type: {type(data).__name__}. Response: {data}"
            )

        if "completion" not in data:
            data["completion"] = self.completion
        if data["completion"] == "KO - TIMEOUT":
            raise TimeoutError("The session has timed out.")
        if data["completion"] == "SOUNDLIKE":
            self.finished = True
            self.win = True
            if not self.id_proposition:
                self.defeat()
        elif "id_proposition" in data:
            self._update(action="win", resp=data)
        else:
            self._update(action="answer", resp=data)
        self.completion = data["completion"]

    def defeat(self):
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
    def confidence(self) -> float:
        return float(self.progression) / 100

    @property
    def akitude_url(self) -> str:
        return f"{self.uri}/assets/img/akitudes_670x1096/{self.akitude}"

    def __str__(self) -> str:
        if self.win and not self.finished:
            return f"{self.proposition_message} {self.name_proposition} ({self.description_proposition})"
        return self.question or ""

    def __repr__(self) -> str:
        return f"Akinator(question={self.question!r}, step={self.step}, progression={self.progression})"
