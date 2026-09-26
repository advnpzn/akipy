"""Shared base class and compiled regex patterns for sync and async Akinator."""

from __future__ import annotations

import html
import json
import os
import re
from typing import Any

import httpx

from .dicts import THEME_ID, THEMES, LANG_MAP
from .exceptions import AkinatorServerError, InvalidLanguageError, InvalidThemeError
from .solver import (
    DEFAULT_SOLVER_TIMEOUT_MS,
    normalize_solver_url,
)

# Compiled once at import time, shared by both subclasses
SESSION_PATTERN = re.compile(r"#session'\).val\('(.+?)'\)")
SIGNATURE_PATTERN = re.compile(r"#signature'\).val\('(.+?)'\)")
IDENTIFIANT_PATTERN = re.compile(r"#identifiant'\).val\('(.+?)'\)")
STORAGE_SESSION_PATTERN = re.compile(r"localStorage\.setItem\('session',\s*'(.+?)'\)")
STORAGE_IDENTIFIANT_PATTERN = re.compile(
    r"localStorage\.setItem\('identifiant',\s*'(.+?)'\)"
)
STORAGE_STEP_PATTERN = re.compile(r"localStorage\.setItem\('step',\s*'(.+?)'\)")
STORAGE_PROGRESSION_PATTERN = re.compile(
    r"localStorage\.setItem\('progression',\s*'(.+?)'\)"
)
QUESTION_PATTERN = re.compile(
    r'<p\b[^>]*\bid="question-label"[^>]*>(.*?)</p>', re.DOTALL
)
PROPOSITION_PATTERN = re.compile(
    r'<p\b[^>]*\bid="p-sub-bubble"[^>]*>(.*?)</p>', re.DOTALL
)
AKITUDE_IMAGE_PATTERN = re.compile(
    r'<img\b[^>]*\bid="akitude"[^>]*\bsrc="([^"]+)"', re.DOTALL
)
WIN_MESSAGE_PATTERN = re.compile(r'<span class="win-sentence">(.+?)<\/span>')
ALREADY_PLAYED_PATTERN = re.compile(r'let tokenDejaJoue = "([\w\s]+)";')
TIMES_SELECTED_PATTERN = re.compile(r'let timesSelected = "(\d+)";')
TIMES_PATTERN = re.compile(r'<span id="timesselected"><\/span>\s+([\w\s]+)<\/span>')
# Chrome/FlareSolverr JSON viewer wraps payload in <pre>...</pre>
_PRE_JSON_PATTERN = re.compile(r"<pre[^>]*>(.*?)</pre>", re.DOTALL | re.IGNORECASE)


def parse_api_json(text: str) -> Any:
    """
    Parse Akinator API JSON from a response body.

    Direct httpx usually returns raw JSON. FlareSolverr (and browsers) may return
    the same payload wrapped in an HTML JSON-viewer page with a ``<pre>`` block.
    """
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Empty response body")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    pre = _PRE_JSON_PATTERN.search(raw)
    if pre:
        inner = html.unescape(pre.group(1)).strip()
        return json.loads(inner)

    # Fallback: first top-level object/array span in the document
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        end = raw.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError("No JSON object found in response body")


class _BaseAkinator:
    """Shared state and pure-Python logic for sync and async Akinator subclasses."""

    _validated_languages: set = set()

    def __init__(
        self,
        solver_url: str | None = None,
        solver_timeout: int = DEFAULT_SOLVER_TIMEOUT_MS,
    ) -> None:
        self.flag_photo: str | int | None = None
        self.photo: str | None = None
        self.pseudo: str | None = None
        self.uri: str | None = None
        self.theme: int | None = None
        self.session: str | None = None
        self.signature: str | None = None
        self.identifiant: str | None = None
        self.child_mode: bool = False
        self._child_mode_str: str = "false"
        self.lang: str | None = None
        self.available_themes: list[str] = []
        self.question: str | None = None
        self.progression: str | None = None
        self.step: str | None = None
        self._answer_depth: int | None = None
        self.akitude: str | None = None
        self.step_last_proposition: str = ""
        self.finished: bool = False
        self.win: bool = False
        self.no_question: bool = False
        self.child_mode_blocked: bool = False
        self.soundlike: bool = False
        self.id_proposition: str = ""
        self.name_proposition: str = ""
        self.description_proposition: str = ""
        self.proposition_message: str = ""
        self.completion: str = "OK"
        # Sync and async subclasses use different httpx client types
        self.client: Any = None
        # Optional challenge solver (FlareSolverr / TRAWL / compatible):
        # constructor arg wins; else AKIPY_SOLVER_URL or AKIPY_FLARESOLVERR_URL env
        raw_solver = (
            solver_url
            if solver_url is not None
            else os.environ.get("AKIPY_SOLVER_URL")
            or os.environ.get("AKIPY_FLARESOLVERR_URL")
        )
        self.solver_url: str | None = normalize_solver_url(raw_solver)
        self.solver_timeout: int = solver_timeout

        # Aliases for older parameter names
        self.flaresolverr_url = self.solver_url
        self.flaresolverr_timeout = self.solver_timeout

    def _set_region(self, lang: str, mode: str) -> None:
        """Resolve and validate language purely from local dicts — no network call."""
        if len(lang) > 2:
            lang = LANG_MAP.get(lang, lang)
        else:
            if lang not in LANG_MAP.values():
                raise InvalidLanguageError(lang)
        self.uri = f"https://{lang}.akinator.com"
        self.lang = lang
        self.available_themes = THEMES.get(lang, [])

        if mode not in self.available_themes:
            raise InvalidThemeError(
                f'Mode "{mode}" is not available in the selected language'
            )

        self.selected_theme = self.available_themes.index(mode)
        self.theme = THEME_ID.get(self.available_themes[self.selected_theme], None)

    def _parse_init_response(self, text: str) -> None:
        """Extract session credentials and first question from the /game HTML response."""
        session_m = STORAGE_SESSION_PATTERN.search(text) or SESSION_PATTERN.search(text)
        signature_m = SIGNATURE_PATTERN.search(text)
        identifiant_m = STORAGE_IDENTIFIANT_PATTERN.search(
            text
        ) or IDENTIFIANT_PATTERN.search(text)
        if not (session_m and identifiant_m):
            raise ValueError(
                "Response does not contain expected data: session or identifiant"
            )
        self.session = session_m.group(1)
        self.signature = signature_m.group(1) if signature_m else None
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

        image_m = AKITUDE_IMAGE_PATTERN.search(text)
        step_m = STORAGE_STEP_PATTERN.search(text)
        progression_m = STORAGE_PROGRESSION_PATTERN.search(text)
        self.step = step_m.group(1) if step_m else "0"
        self._answer_depth = 0
        self.progression = progression_m.group(1) if progression_m else "0.00000"
        self.akitude = image_m.group(1).rsplit("/", 1)[-1] if image_m else "defi.png"
        self.win = False
        self.finished = False
        self.no_question = False
        self.child_mode_blocked = False
        self.soundlike = False
        self.step_last_proposition = ""
        self.completion = "OK"

    def _base_data(self) -> dict:
        """Common form fields shared across answer/back/exclude requests."""
        data = {
            "step": self.step,
            "progression": self.progression,
            "sid": self.theme,
            "cm": self._child_mode_str,
            "session": self.session,
        }
        if self.signature is not None:
            data["signature"] = self.signature
        return data

    def _update(self, action: str, resp: dict) -> None:
        if action == "answer":
            self.win = False
            self.no_question = False
            self.id_proposition = ""
            self.akitude = resp.get("akitude", self.akitude)
            self.step = resp.get("step", self.step)
            self.progression = resp.get("progression", self.progression)
            self.question = html.unescape(resp.get("question", ""))
        elif action == "win":
            self.win = True
            self.step_last_proposition = str(resp.get("step", self.step or ""))
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
            self.no_question = str(resp.get("no_question", "0")) == "1"
            self.child_mode_blocked = str(resp.get("valide_contrainte", "1")) == "0"
            if self.child_mode_blocked:
                self.win = False
                self.finished = True
                self.id_proposition = ""
                self.name_proposition = ""
                self.description_proposition = ""
                self.pseudo = None
                self.photo = None
                self.flag_photo = None
        else:
            raise NotImplementedError(f"Unable to handle action: {action}")

    def handle_response(self, resp: httpx.Response) -> None:
        """Parse an API response and update game state. Used by both sync and async paths."""
        resp.raise_for_status()
        raw_text = getattr(resp, "text", "")
        text = raw_text if isinstance(raw_text, str) else ""

        data: Any
        try:
            if text.strip():
                data = parse_api_json(text)
            else:
                # No usable body string: unit-test mocks often only set .json()
                data = resp.json()
        except Exception as e:
            if "A technical problem has occurred." in text:
                raise RuntimeError(
                    f"A technical problem has occurred. Response: {text[:500]}"
                ) from e
            content_type = getattr(resp, "headers", {}).get("content-type", "")
            if not isinstance(content_type, str):
                content_type = ""
            content_type = content_type.lower()
            if "text/html" in content_type or "<html" in text.lower():
                raise RuntimeError(
                    f"Server returned HTML instead of JSON. This typically means the session has expired "
                    f"or there was a server error. Response preview: {text[:500]}"
                ) from e
            raise RuntimeError(
                f"Failed to parse JSON response. Error: {e}. "
                f"Response (first 500 chars): {text[:500]}"
            ) from e

        if isinstance(data, list) and len(data) == 0:
            raise RuntimeError("No more characters available to propose")
        if not isinstance(data, dict):
            raise RuntimeError(
                f"Unexpected response type: {type(data).__name__}. Response: {data}"
            )

        if "completion" not in data:
            if "question" not in data and "id_proposition" not in data:
                raise AkinatorServerError("Akinator returned no game result")
            data["completion"] = self.completion
        if data["completion"] == "KO - TIMEOUT":
            raise TimeoutError("The session has timed out.")
        if data["completion"] == "KO":
            raise AkinatorServerError(
                "Akinator rejected the game request (session expired or game state out of sync)"
            )
        if data["completion"] == "SOUNDLIKE":
            self.finished = True
            self.win = False
            self.soundlike = True
        elif "id_proposition" in data:
            self._update(action="win", resp=data)
        else:
            self._update(action="answer", resp=data)
        self.completion = data["completion"]

    def handle_soundlike_transition(self, resp: httpx.Response) -> None:
        """Handle the terminal /exclude response when no questions remain."""
        resp.raise_for_status()
        try:
            data = parse_api_json(resp.text)
        except ValueError as e:
            raise AkinatorServerError(
                "Akinator returned an invalid terminal response"
            ) from e
        if (
            not isinstance(data, dict)
            or data.get("completion") == "KO"
            or "step" not in data
        ):
            raise AkinatorServerError("Akinator rejected the terminal game request")
        self.step = data["step"]
        self.win = False
        self.finished = True
        self.soundlike = True
        self.id_proposition = ""
        self.completion = "SOUNDLIKE"

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
        return float(self.progression or 0) / 100

    @property
    def akitude_url(self) -> str:
        return f"{self.uri}/assets/img/akitudes_670x1096/{self.akitude}"

    @property
    def akinator_image_url(self) -> str:
        """URL of the last known PNG fallback image for Akinator."""
        return self.akitude_url

    def __str__(self) -> str:
        if self.win and not self.finished:
            return f"{self.proposition_message} {self.name_proposition} ({self.description_proposition})"
        return self.question or ""

    def __repr__(self) -> str:
        return f"Akinator(question={self.question!r}, step={self.step}, progression={self.progression})"
