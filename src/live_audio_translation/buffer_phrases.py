"""Prepare finalized English ASR events for the local translation worker.

The module is an NDJSON stdin/stdout filter. It joins short transcript events
into punctuation-delimited phrases, keeps timing/source metadata, and flushes
unfinished text after a bounded wait so live output does not stall.
"""

from __future__ import annotations

import argparse
import json
import queue
import re
import sys
import threading
import time
from collections.abc import Mapping
from typing import Any, TextIO

from live_audio_translation.process_identity import set_demo_process_title


SENTENCE_END = re.compile(r"[.!?][\"')\]]*")
WORD = re.compile(r"\S+")
SENTINEL = object()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Buffer English ASR JSON events into translation-ready phrases."
    )
    parser.add_argument(
        "--max-wait-seconds", type=float, default=5.0,
        help="Maximum time to hold unfinished text (default: 5).",
    )
    return parser.parse_args()


def normalized_word(token: str) -> str:
    return re.sub(r"[^\w']", "", token).lower()


def has_sentence_end(token: str) -> bool:
    return bool(SENTENCE_END.search(token))


def trim_repeated_boundary(previous: str, current: str) -> str:
    """Remove a likely one-word duplicate left by overlapping ASR windows."""
    previous_tokens = WORD.findall(previous)
    current_tokens = WORD.findall(current)
    if not previous_tokens or not current_tokens:
        return current
    prior, upcoming = previous_tokens[-1], current_tokens[0]
    if (
        normalized_word(prior)
        and normalized_word(prior) == normalized_word(upcoming)
        and (has_sentence_end(prior) or has_sentence_end(upcoming))
    ):
        return current[len(upcoming) :].lstrip()
    return current


class PhraseBuffer:
    """Accumulate English events and emit translation-ready phrase events."""

    def __init__(self) -> None:
        self.text = ""
        self.source_ids: list[Any] = []
        self.start_ms: Any = None
        self.end_ms: Any = None
        self.first_received_at: float | None = None
        self.sequence = 0
        self.previous_input = ""

    def add(self, event: Mapping[str, Any], now: float) -> list[dict[str, Any]]:
        """Append one finalized ASR event and release any complete sentence."""
        raw_input = event["text"].strip()
        incoming = trim_repeated_boundary(self.previous_input, raw_input)
        self.previous_input = raw_input
        if not incoming:
            return []
        self.text = f"{self.text} {incoming}".strip()
        self._add_metadata(event, now)
        return self.release_completed(now)

    def _add_metadata(self, event: Mapping[str, Any], now: float) -> None:
        if self.first_received_at is None:
            self.first_received_at = now
        if "id" in event:
            self.source_ids.append(event["id"])
        if self.start_ms is None and "start_ms" in event:
            self.start_ms = event["start_ms"]
        if "end_ms" in event:
            self.end_ms = event["end_ms"]

    def release_completed(self, now: float) -> list[dict[str, Any]]:
        matches = list(SENTENCE_END.finditer(self.text))
        if not matches:
            return []
        boundary = matches[-1].end()
        event = self._event(self.text[:boundary].strip())
        tail = self.text[boundary:].strip()
        if tail:
            self.text = tail
            self.first_received_at = now
        else:
            self._reset("", now)
        return [event]

    def flush(self) -> dict[str, Any] | None:
        """Emit remaining unfinished text, typically at timeout or end of input."""
        if not self.text:
            return None
        event = self._event(self.text)
        self._reset("", time.monotonic())
        return event

    def expired(self, now: float, max_wait_seconds: float) -> bool:
        return self.first_received_at is not None and now - self.first_received_at >= max_wait_seconds

    def _event(self, text: str) -> dict[str, Any]:
        self.sequence += 1
        result: dict[str, Any] = {
            "id": f"phrase-{self.sequence}", "source_ids": self.source_ids.copy(), "text": text,
        }
        if self.start_ms is not None:
            result["start_ms"] = self.start_ms
        if self.end_ms is not None:
            result["end_ms"] = self.end_ms
        return result

    def _reset(self, tail: str, now: float) -> None:
        self.text, self.source_ids = tail, []
        self.start_ms = self.end_ms = None
        self.first_received_at = now if tail else None


def read_lines(input_stream: TextIO, lines: queue.Queue[object]) -> None:
    for line in input_stream:
        lines.put(line)
    lines.put(SENTINEL)


def write_event(event: Mapping[str, Any], output_stream: TextIO) -> None:
    output_stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    output_stream.flush()


def valid_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    if not isinstance(value.get("text"), str) or not value["text"].strip():
        raise ValueError("input event requires a non-empty string 'text' field")
    return value


def run(max_wait_seconds: float, *, input_stream: TextIO = sys.stdin, output_stream: TextIO = sys.stdout, error_stream: TextIO = sys.stderr) -> None:
    """Run the long-lived NDJSON phrase-buffer process until input closes."""
    lines: queue.Queue[object] = queue.Queue()
    threading.Thread(target=read_lines, args=(input_stream, lines), daemon=True).start()
    buffer = PhraseBuffer()
    line_number = 0
    while True:
        try:
            line = lines.get(timeout=0.1)
        except queue.Empty:
            if buffer.expired(time.monotonic(), max_wait_seconds):
                event = buffer.flush()
                if event:
                    write_event(event, output_stream)
            continue
        if line is SENTINEL:
            event = buffer.flush()
            if event:
                write_event(event, output_stream)
            return
        line_number += 1
        if not isinstance(line, str) or not line.strip():
            continue
        try:
            input_event = valid_event(json.loads(line))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping input line {line_number}: {error}", file=error_stream)
            continue
        for event in buffer.add(input_event, time.monotonic()):
            write_event(event, output_stream)


def main() -> None:
    set_demo_process_title()
    args = parse_args()
    if args.max_wait_seconds <= 0:
        print("--max-wait-seconds must be greater than zero.", file=sys.stderr)
        raise SystemExit(2)
    try:
        run(args.max_wait_seconds)
    except KeyboardInterrupt:
        print("Phrase buffer stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
