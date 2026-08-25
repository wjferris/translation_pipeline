"""Bounded, in-memory context helpers for local ASR and translation workers."""

from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass


DEFAULT_WHISPER_CONTEXT_PHRASES = 1
DEFAULT_TRANSLATION_CONTEXT_PHRASES = 2
WHISPER_CONTEXT_MAX_CHARS = 320
TRANSLATION_CONTEXT_MAX_CHARS = 1_200


def is_non_speech_cue(text: str) -> bool:
    """Return whether text consists only of bracketed non-speech cue labels."""
    return bool(re.fullmatch(r"(?:\s*\[[^\]]+\]\s*)+", text))


def _tail_at_word_boundary(text: str, maximum: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= maximum:
        return normalized
    tail = normalized[-maximum:]
    separator = tail.find(" ")
    return tail[separator + 1 :] if separator >= 0 else tail


class EnglishContext:
    """Keep finalized English ASR text for a bounded Whisper decoder prompt."""

    def __init__(self, phrase_limit: int, *, maximum_chars: int = WHISPER_CONTEXT_MAX_CHARS) -> None:
        self.phrase_limit = phrase_limit
        self.maximum_chars = maximum_chars
        self._phrases: deque[str] = deque()

    def add(self, text: str) -> None:
        if self.phrase_limit > 0 and text.strip() and not is_non_speech_cue(text):
            self._phrases.append(" ".join(text.split()))

    def prompt(self) -> str | None:
        if self.phrase_limit <= 0:
            return None
        phrases = list(self._phrases)[-self.phrase_limit :]
        if not phrases:
            return None
        return _tail_at_word_boundary("\n".join(phrases), self.maximum_chars) or None


@dataclass(frozen=True)
class TranslationPair:
    """One completed English source phrase and its emitted Spanish translation."""

    english: str
    spanish: str


class TranslationContext:
    """Keep recent successful phrase pairs for an Ollama chat request."""

    def __init__(
        self, phrase_limit: int, *, maximum_chars: int = TRANSLATION_CONTEXT_MAX_CHARS
    ) -> None:
        self.phrase_limit = phrase_limit
        self.maximum_chars = maximum_chars
        self._pairs: deque[TranslationPair] = deque()

    def add(self, english: str, spanish: str) -> None:
        if (
            self.phrase_limit > 0
            and english.strip()
            and spanish.strip()
            and not is_non_speech_cue(english)
            and not is_non_speech_cue(spanish)
        ):
            self._pairs.append(TranslationPair(" ".join(english.split()), " ".join(spanish.split())))

    def pairs(self) -> list[TranslationPair]:
        if self.phrase_limit <= 0:
            return []
        selected: list[TranslationPair] = []
        used = 0
        for pair in reversed(list(self._pairs)[-self.phrase_limit :]):
            size = len(pair.english) + len(pair.spanish)
            if selected and used + size > self.maximum_chars:
                break
            if not selected and size > self.maximum_chars:
                half = max(1, self.maximum_chars // 2)
                pair = TranslationPair(
                    _tail_at_word_boundary(pair.english, half),
                    _tail_at_word_boundary(pair.spanish, half),
                )
                size = len(pair.english) + len(pair.spanish)
            selected.append(pair)
            used += size
        return list(reversed(selected))
