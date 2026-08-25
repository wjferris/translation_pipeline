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

from live_audio_translation.phrase_context import (
    DEFAULT_TRANSLATION_CONTEXT_PHRASES,
    TranslationContext,
)


DEFAULT_MODEL = "translategemma:4b"
PROMPT = (
    "Translate the following English into natural Spanish. "
    "Return only the Spanish translation, with no explanation, labels, quotes, "
    "or Markdown.\n\nEnglish:\n"
)
CONTEXT_INSTRUCTION = (
    "Translate the final English phrase into natural Spanish. Prior English and Spanish "
    "messages are context only. Return only the Spanish translation of the final phrase, "
    "with no explanation, labels, quotes, or Markdown."
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
    parser.add_argument(
        "--translation-context-phrases",
        type=int,
        default=DEFAULT_TRANSLATION_CONTEXT_PHRASES,
        help="Completed English/Spanish phrase pairs supplied as chat context (default: 2; 0 disables).",
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


def translation_messages(text: str, context: TranslationContext | None = None) -> list[dict[str, str]]:
    """Build a bounded chat history that keeps the current source phrase distinct."""
    pairs = context.pairs() if context is not None else []
    if not pairs:
        return [{"role": "user", "content": PROMPT + text}]
    messages = [{"role": "system", "content": CONTEXT_INSTRUCTION}]
    for pair in pairs:
        messages.extend([
            {"role": "user", "content": f"Previous English phrase (context only):\n{pair.english}"},
            {"role": "assistant", "content": pair.spanish},
        ])
    messages.append({"role": "user", "content": f"Current English phrase:\n{text}"})
    return messages


def translate(
    client: Client, model: str, text: str, *, context: TranslationContext | None = None
) -> str:
    """Request a Spanish-only translation from the selected local Ollama model."""
    response = client.chat(
        model=model,
        messages=translation_messages(text, context),
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
    context_phrases: int = DEFAULT_TRANSLATION_CONTEXT_PHRASES,
) -> None:
    """Run the long-lived ordered English-to-Spanish NDJSON worker."""
    context = TranslationContext(context_phrases)
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
            spanish_text = translate(client, model, event["text"], context=context)
        except Exception as error:  # The client exposes several transport/model errors.
            message = f"Translation failed: {error}"
            print(f"Input line {line_number}: {message}", file=error_stream)
            write_event(event_error(event, message), output_stream)
            continue

        result = dict(event)
        result["text"] = spanish_text
        write_event(result, output_stream)
        context.add(event["text"], spanish_text)


def main() -> None:
    args = parse_args()
    if args.translation_context_phrases < 0:
        print("--translation-context-phrases must be zero or greater.", file=sys.stderr)
        raise SystemExit(2)
    try:
        print(
            f"Translation context: {args.translation_context_phrases} completed phrase pair(s).",
            file=sys.stderr,
        )
        run(Client(), args.model, context_phrases=args.translation_context_phrases)
    except KeyboardInterrupt:
        print("Translation worker stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
