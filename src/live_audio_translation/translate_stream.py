"""Translate finalized English NDJSON events using local Ollama inference.

The process reads one event per stdin line and writes one Spanish event per
stdout line. It deliberately keeps diagnostics on stderr so its output can be
piped directly into a future text-to-speech stage.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from typing import Any, TextIO

from ollama import Client


DEFAULT_MODEL = "translategemma:4b"
PROMPT = (
    "Translate the following English into natural Spanish. "
    "Return only the Spanish translation, with no explanation, labels, quotes, "
    "or Markdown.\n\nEnglish:\n"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Translate newline-delimited English JSON events to Spanish."
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Local Ollama model to use (default: {DEFAULT_MODEL}).",
    )
    return parser.parse_args()


def write_event(event: Mapping[str, Any], output: TextIO) -> None:
    output.write(json.dumps(event, ensure_ascii=False) + "\n")
    output.flush()


def event_error(event: Mapping[str, Any], message: str) -> dict[str, Any]:
    result: dict[str, Any] = {"error": message}
    for field in ("id", "start_ms", "end_ms"):
        if field in event:
            result[field] = event[field]
    return result


def validate_event(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")

    text = value.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("input event requires a non-empty string 'text' field")
    return value


def translate(client: Client, model: str, text: str) -> str:
    """Request a Spanish-only translation from the selected local Ollama model."""
    response = client.chat(
        model=model,
        messages=[{"role": "user", "content": PROMPT + text}],
        options={"temperature": 0},
    )
    content = response.message.content.strip()
    if not content:
        raise RuntimeError("Ollama returned an empty translation")
    return content


def run(
    client: Client,
    model: str,
    *,
    input_stream: TextIO = sys.stdin,
    output_stream: TextIO = sys.stdout,
    error_stream: TextIO = sys.stderr,
) -> None:
    """Run the long-lived ordered English-to-Spanish NDJSON worker."""
    for line_number, raw_line in enumerate(input_stream, start=1):
        if not raw_line.strip():
            continue

        event: dict[str, Any] | None = None
        try:
            event = validate_event(json.loads(raw_line))
        except (json.JSONDecodeError, ValueError) as error:
            print(f"Skipping input line {line_number}: {error}", file=error_stream)
            continue

        try:
            spanish_text = translate(client, model, event["text"])
        except Exception as error:  # The client exposes several transport/model errors.
            message = f"Translation failed: {error}"
            print(f"Input line {line_number}: {message}", file=error_stream)
            write_event(event_error(event, message), output_stream)
            continue

        result = dict(event)
        result["text"] = spanish_text
        write_event(result, output_stream)


def main() -> None:
    args = parse_args()
    try:
        run(Client(), args.model)
    except KeyboardInterrupt:
        print("Translation worker stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
