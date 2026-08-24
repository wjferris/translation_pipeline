"""Run a local browser demonstration of English-to-Spanish live translation.

This command is intentionally additive. It starts the existing microphone and
phrase-buffer CLI stages, then fans finalized events to a loopback-only browser
display, local Ollama translation, and local Piper speaker output. The normal
NDJSON command-line pipeline remains available for troubleshooting.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from collections.abc import Iterator
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from ollama import Client
from piper.voice import PiperVoice

from live_audio_translation.process_identity import PROCESS_TITLE_ENV, set_demo_process_title
from live_audio_translation.speak_stream import DEFAULT_MODEL_PATH, play_text
from live_audio_translation.timing_trace import TRACE_TIMEBASE_ENV, TraceRun, run_configuration
from live_audio_translation.transcribe_whisper import (
    default_whisper_model,
    validate_silero_vad,
)
from live_audio_translation.translate_stream import DEFAULT_MODEL, translate


RESOURCE_DIR = Path(__file__).resolve().parents[1] / "resources"
FAVICON_PATH = RESOURCE_DIR / "images" / "babelfish_favicon.png"
WEB_DIR = RESOURCE_DIR / "web"
STATIC_ASSETS = {
    "/": (WEB_DIR / "index.html", "text/html; charset=utf-8"),
    "/index.html": (WEB_DIR / "index.html", "text/html; charset=utf-8"),
    "/assets/demo.css": (WEB_DIR / "demo.css", "text/css; charset=utf-8"),
    "/assets/demo.js": (WEB_DIR / "demo.js", "text/javascript; charset=utf-8"),
    "/assets/babelfish_favicon.png": (FAVICON_PATH, "image/png"),
}

class DemoState:
    """Thread-safe, bounded event history for local browser clients."""

    def __init__(self) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=200)
        self._next_id = 1
        self._condition = threading.Condition()
        self._closed = False

    def publish(self, kind: str, text: str) -> None:
        """Record and wake clients waiting for a display event."""
        with self._condition:
            self._events.append({"event_id": self._next_id, "kind": kind, "text": text})
            self._next_id += 1
            self._condition.notify_all()

    def events_after(self, event_id: int, timeout: float = 15.0) -> list[dict[str, Any]]:
        """Wait briefly for new events, returning the bounded event history delta."""
        with self._condition:
            self._condition.wait_for(
                lambda: self._closed
                or bool(self._events and self._events[-1]["event_id"] > event_id),
                timeout=timeout,
            )
            return [event for event in self._events if event["event_id"] > event_id]

    def close(self) -> None:
        """Wake browser clients so Server-Sent Event handlers can exit promptly."""
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    @property
    def closed(self) -> bool:
        """Return whether the browser event stream is shutting down."""
        with self._condition:
            return self._closed


def make_handler(state: DemoState) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to one demo state instance."""

    class DemoHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
            asset = STATIC_ASSETS.get(self.path)
            if asset is not None:
                asset_path, content_type = asset
                body = asset_path.read_bytes()
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(body)
                return
            if self.path == "/events":
                self._send_events()
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def _send_events(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            last_event = 0
            try:
                while True:
                    events = state.events_after(last_event)
                    if not events:
                        if state.closed:
                            return
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
                        continue
                    for event in events:
                        message = json.dumps(event, ensure_ascii=False).encode("utf-8")
                        self.wfile.write(b"data: " + message + b"\n\n")
                        last_event = event["event_id"]
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                return

        def log_message(self, _format: str, *_args: object) -> None:
            """Keep routine browser requests out of the operator terminal."""

    return DemoHandler


class DemoHTTPServer(ThreadingHTTPServer):
    """Loopback HTTP server whose display-only request threads never own audio work."""

    daemon_threads = True


def parse_args() -> argparse.Namespace:
    """Parse demo presentation, ASR, translation, and Piper settings."""
    parser = argparse.ArgumentParser(
        description="Run the local browser English-to-Spanish translation demo."
    )
    parser.add_argument("--port", type=int, default=8765, help="Local browser port (default: 8765).")
    parser.add_argument("--no-open-browser", action="store_true", help="Print the local URL without opening it.")
    parser.add_argument("--no-timing-trace", action="store_true", help="Disable the default timing trace for a controlled baseline run.")
    parser.add_argument("--language", default="en", help="Spoken input language (default: en).")
    parser.add_argument(
        "--segmentation", choices=("fixed", "vad"), default="vad", help="ASR segmentation method (default: vad)."
    )
    parser.add_argument(
        "--vad-backend", choices=("webrtc", "silero"), default="webrtc",
        help="Local VAD backend for --segmentation vad (default: webrtc).",
    )
    parser.add_argument("--silero-threshold", type=float, default=0.5, help="Stateful Silero speech confidence (default: 0.5).")
    parser.add_argument("--silero-min-silence-seconds", type=float, default=0.3, help="Stateful Silero phrase-end silence (default: 0.3).")
    parser.add_argument("--silero-speech-pad-seconds", type=float, default=0.1, help="Stateful Silero recognition padding (default: 0.1).")
    parser.add_argument("--silero-max-phrase-seconds", type=float, default=10.0, help="Stateful Silero maximum phrase (default: 10).")
    parser.add_argument("--window-seconds", type=float, default=5.0, help="Fixed-window duration (default: 5).")
    parser.add_argument("--stride-seconds", type=float, default=4.0, help="Fixed-window stride (default: 4).")
    parser.add_argument("--vad-silence-seconds", type=float, default=0.45, help="VAD phrase-end silence (default: 0.45).")
    parser.add_argument("--vad-aggressiveness", type=int, default=2, help="WebRTC VAD aggressiveness 0-3 (default: 2).")
    parser.add_argument("--vad-pre-roll-seconds", type=float, default=0.3, help="VAD pre-roll (default: 0.3).")
    parser.add_argument("--vad-min-phrase-seconds", type=float, default=0.7, help="Minimum VAD phrase (default: 0.7).")
    parser.add_argument("--vad-max-phrase-seconds", type=float, default=10.0, help="Maximum VAD phrase (default: 10).")
    parser.add_argument("--input-gain-db", type=float, default=0.0, help="Local microphone gain in dB from -48 through +48 (default: 0).")
    parser.add_argument("--max-wait-seconds", type=float, default=5.0, help="Phrase buffer maximum wait (default: 5).")
    parser.add_argument("--translation-model", default=DEFAULT_MODEL, help=f"Local Ollama model (default: {DEFAULT_MODEL}).")
    parser.add_argument("--piper-model", type=Path, default=DEFAULT_MODEL_PATH, help=f"Local Piper .onnx voice (default: {DEFAULT_MODEL_PATH}).")
    parser.add_argument("--output-device", help="Sounddevice output device name or index for Spanish audio.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """Fail early for unavailable local dependencies and invalid demo settings."""
    if not 1 <= args.port <= 65535:
        raise ValueError("--port must be between 1 and 65535.")
    if not args.piper_model.is_file():
        raise ValueError(f"Piper voice model not found: {args.piper_model}")
    whisper_model = Path(os.environ.get("WHISPER_MODEL_PATH", default_whisper_model()))
    if not whisper_model.is_file():
        raise ValueError(f"Whisper model file not found: {whisper_model}")
    if shutil.which("whisper") is None:
        raise ValueError("Whisper executable not found on PATH.")
    if args.segmentation != "vad" and args.vad_backend != "webrtc":
        raise ValueError("--vad-backend is only valid with --segmentation vad.")
    if args.max_wait_seconds <= 0:
        raise ValueError("--max-wait-seconds must be greater than zero.")
    if not -48 <= args.input_gain_db <= 48:
        raise ValueError("--input-gain-db must be between -48 and 48.")


def microphone_command(args: argparse.Namespace) -> list[str]:
    """Build an unchanged microphone CLI invocation that emits English NDJSON."""
    command = [
        sys.executable, "-m", "live_audio_translation.transcribe_microphone",
        "--segmentation", args.segmentation,
        "--language", args.language,
        "--output-format", "ndjson",
    ]
    if args.segmentation == "vad":
        command.extend(["--vad-backend", args.vad_backend])
        if args.vad_backend == "webrtc":
            command.extend([
                "--vad-silence-seconds", str(args.vad_silence_seconds),
                "--vad-aggressiveness", str(args.vad_aggressiveness),
                "--vad-pre-roll-seconds", str(args.vad_pre_roll_seconds),
                "--vad-min-phrase-seconds", str(args.vad_min_phrase_seconds),
                "--vad-max-phrase-seconds", str(args.vad_max_phrase_seconds),
            ])
        else:
            command.extend(["--silero-threshold", str(args.silero_threshold), "--silero-min-silence-seconds", str(args.silero_min_silence_seconds), "--silero-speech-pad-seconds", str(args.silero_speech_pad_seconds), "--silero-max-phrase-seconds", str(args.silero_max_phrase_seconds)])
    else:
        command.extend(["--window-seconds", str(args.window_seconds), "--stride-seconds", str(args.stride_seconds)])
    if args.input_gain_db:
        command.extend(["--input-gain-db", str(args.input_gain_db)])
    return command


def iter_json_lines(stream: Iterator[str]) -> Iterator[dict[str, Any]]:
    """Yield valid event objects from a CLI worker's NDJSON standard output."""
    for line in stream:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            print(f"Demo skipped malformed worker output: {line.strip()}", file=sys.stderr)
            continue
        if isinstance(value, dict) and isinstance(value.get("text"), str) and value["text"].strip():
            yield value


class DemoPipeline:
    """Fan out local ASR events to the display, translation, and Piper speech."""

    def __init__(
        self, args: argparse.Namespace, state: DemoState, voice: PiperVoice, trace: TraceRun | None
    ) -> None:
        self.args, self.state, self.voice = args, state, voice
        self.trace = trace
        self.stop_event = threading.Event()
        self.microphone: subprocess.Popen[str] | None = None
        self.buffer: subprocess.Popen[str] | None = None
        self.english_thread: threading.Thread | None = None
        self.spanish_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the existing ASR and phrase-buffer workers plus fan-out threads."""
        worker_environment = dict(os.environ)
        if self.trace is not None:
            worker_environment[TRACE_TIMEBASE_ENV] = str(self.trace.timebase_ns)
        else:
            worker_environment.pop(TRACE_TIMEBASE_ENV, None)
        self.buffer = subprocess.Popen(
            [sys.executable, "-m", "live_audio_translation.buffer_phrases", "--max-wait-seconds", str(self.args.max_wait_seconds)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1,
            env={**worker_environment, PROCESS_TITLE_ENV: "BabelFish Phrase Buffer"},
        )
        self.microphone = subprocess.Popen(
            microphone_command(self.args), stdout=subprocess.PIPE, text=True, bufsize=1,
            env={**worker_environment, PROCESS_TITLE_ENV: "BabelFish ASR"},
        )
        self.english_thread = threading.Thread(target=self._forward_english, name="demo-english")
        self.spanish_thread = threading.Thread(target=self._translate_and_speak, name="demo-spanish")
        self.english_thread.start()
        self.spanish_thread.start()

    def _forward_english(self) -> None:
        assert self.microphone is not None and self.microphone.stdout is not None
        assert self.buffer is not None and self.buffer.stdin is not None
        try:
            for event in iter_json_lines(self.microphone.stdout):
                if self.stop_event.is_set():
                    return
                if self.trace is not None:
                    self.trace.stage("asr", event)
                self.state.publish("english", event["text"])
                self.buffer.stdin.write(json.dumps(event, ensure_ascii=False) + "\n")
                self.buffer.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            if not self.stop_event.is_set():
                self.state.publish("status", f"English input stopped: {error}")
        finally:
            try:
                self.buffer.stdin.close()
            except (BrokenPipeError, OSError):
                pass

    def _translate_and_speak(self) -> None:
        assert self.buffer is not None and self.buffer.stdout is not None
        client = Client()
        for event in iter_json_lines(self.buffer.stdout):
            if self.stop_event.is_set():
                return
            timing: dict[str, Any] | None = None
            if self.trace is not None:
                self.trace.stage("phrases", event)
                timing = copy.deepcopy(event.get("timing", {}))
                if not isinstance(timing, dict):
                    timing = {}
                phrase_id = timing.get("phrase_id", event.get("id"))
                source_segment_ids = timing.get("source_segment_ids", event.get("source_ids", []))
                timestamps = timing.setdefault("timestamps_ns", {})
                timestamps["translation_start"] = self.trace.now_ns()
                timing["phrase_id"] = phrase_id
                timing["source_segment_ids"] = source_segment_ids
                timing.setdefault("queue_depths", {})["translation"] = {
                    "physical": None,
                    "logical_pending": 1,
                }
            self.state.publish("status", "Translating…")
            try:
                spanish = translate(client, self.args.translation_model, event["text"])
            except Exception as error:
                print(f"Translation failed: {error}", file=sys.stderr)
                self.state.publish("status", "Translation unavailable — see operator terminal.")
                continue
            translated_event: dict[str, Any] | None = None
            if self.trace is not None and timing is not None:
                timing["timestamps_ns"]["translation_complete"] = self.trace.now_ns()
                translated_event = {
                    "id": event.get("id"),
                    "source_ids": event.get("source_ids", []),
                    "start_ms": event.get("start_ms"),
                    "end_ms": event.get("end_ms"),
                    "text": spanish,
                    "timing": timing,
                }
                self.trace.stage("translations", translated_event)
            self.state.publish("spanish", spanish)
            self.state.publish("status", "Speaking Spanish…")
            playback_event = copy.deepcopy(translated_event) if translated_event is not None else None
            if playback_event is not None:
                playback_event["timing"].setdefault("queue_depths", {})["tts_playback"] = {
                    "physical": None,
                    "logical_pending": 1,
                }

            def mark_timing(boundary: str) -> None:
                if playback_event is not None and self.trace is not None:
                    playback_event["timing"]["timestamps_ns"][boundary] = self.trace.now_ns()

            try:
                play_text(
                    self.voice,
                    spanish,
                    self.args.output_device,
                    on_timing=mark_timing if playback_event is not None else None,
                )
            except Exception as error:
                if self.trace is not None and playback_event is not None:
                    self.trace.stage("playback", playback_event)
                print(f"Spanish audio failed: {error}", file=sys.stderr)
                self.state.publish("status", "Audio unavailable — see operator terminal.")
                continue
            if self.trace is not None and playback_event is not None:
                self.trace.stage("playback", playback_event)
            self.state.publish("status", "Listening…")

    def stop(self) -> None:
        """Stop intake, then wait for Piper/native audio work to return safely."""
        self.stop_event.set()
        self.state.publish("status", "Stopping input — finishing current Spanish phrase…")
        for process in (self.microphone, self.buffer):
            if process is not None and process.poll() is None:
                process.terminate()
        for process in (self.microphone, self.buffer):
            if process is not None:
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for worker in (self.english_thread, self.spanish_thread):
            if worker is not None and worker.is_alive():
                worker.join()


def main() -> None:
    """Start the fully local browser demo and stop it cleanly on Ctrl-C."""
    set_demo_process_title("BabelFish Demo")
    args = parse_args()
    try:
        validate_args(args)
    except ValueError as error:
        print(f"Demo cannot start: {error}", file=sys.stderr)
        raise SystemExit(2) from error

    trace: TraceRun | None = None
    try:
        voice = PiperVoice.load(args.piper_model)
        state = DemoState()
        state.publish("status", "Loading local translation demo…")
        server = DemoHTTPServer(("127.0.0.1", args.port), make_handler(state))
        if not args.no_timing_trace:
            trace = TraceRun.create(run_configuration(args))
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Demo cannot start: {error}", file=sys.stderr)
        raise SystemExit(2) from error

    pipeline = DemoPipeline(args, state, voice, trace)
    url = f"http://127.0.0.1:{args.port}"
    run_status = "completed"
    try:
        pipeline.start()
        state.publish("status", "Listening…")
        if trace is not None:
            print(f"Timing trace: {trace.directory}", file=sys.stderr)
        print(f"Local demo running at {url}. Press Ctrl-C to stop.", file=sys.stderr)
        print(
            f"BabelFish session and process group: {os.getpgrp()} (demo PID {os.getpid()}; "
            "ASR and phrase buffer inherit this isolated group).",
            file=sys.stderr,
        )
        if not args.no_open_browser:
            webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        run_status = "interrupted"
        print("\nStopping local browser demo...", file=sys.stderr)
    finally:
        pipeline.stop()
        if trace is not None:
            trace.close(run_status)
            if trace.diagnostic_error:
                print(f"Timing trace incomplete: {trace.diagnostic_error}", file=sys.stderr)
        state.close()
        server.shutdown()
        server.server_close()
        print("Local browser demo stopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
