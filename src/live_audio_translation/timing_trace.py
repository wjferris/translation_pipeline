"""Low-impact, local timing traces for browser-demo runs."""

from __future__ import annotations

import json
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


TRACE_ROOT = Path("/tmp/babelfish-live-runs")
TRACE_TIMEBASE_ENV = "BABELFISH_TRACE_TIMEBASE_NS"
TRACE_QUEUE_SIZE = 2_048
TIMESTAMP_FIELDS = (
    "source_audio_start",
    "source_audio_end",
    "vad_detected_start",
    "vad_segment_closed",
    "asr_start",
    "asr_complete",
    "translation_start",
    "translation_complete",
    "tts_start",
    "tts_first_audio",
    "tts_complete",
    "playback_start",
    "playback_complete",
)
_SENTINEL = object()


def trace_timebase_from_environment() -> int | None:
    """Return the demo timebase exported to a child worker, if any."""
    value = os.environ.get(TRACE_TIMEBASE_ENV)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def relative_monotonic_ns(timebase_ns: int | None) -> int | None:
    """Return the current session-relative monotonic timestamp."""
    if timebase_ns is None:
        return None
    return max(0, time.monotonic_ns() - timebase_ns)


def empty_timestamps() -> dict[str, int | None]:
    """Create the stable timestamp schema with unavailable fields set to null."""
    return {field: None for field in TIMESTAMP_FIELDS}


def milliseconds(start_ns: int | None, end_ns: int | None) -> float | None:
    """Convert an available monotonic interval to milliseconds."""
    if start_ns is None or end_ns is None:
        return None
    return (end_ns - start_ns) / 1_000_000


def latency_slope_ms_per_second(records: list[Mapping[str, Any]]) -> float | None:
    """Estimate cumulative playback-start delay growth from saved segment metrics."""
    points = [
        (record.get("source_end_ms"), record.get("derived_metrics", {}).get("end_to_end_playback_start_ms"))
        for record in records
    ]
    usable = [(float(source), float(latency)) for source, latency in points if source is not None and latency is not None]
    if len(usable) < 2:
        return None
    mean_source = sum(source for source, _ in usable) / len(usable)
    mean_latency = sum(latency for _, latency in usable) / len(usable)
    denominator = sum((source - mean_source) ** 2 for source, _ in usable)
    if denominator == 0:
        return None
    slope_per_ms = sum(
        (source - mean_source) * (latency - mean_latency) for source, latency in usable
    ) / denominator
    return slope_per_ms * 1_000


def run_configuration(args: Any) -> dict[str, Any]:
    """Capture JSON-safe demo configuration without retaining environment secrets."""
    result: dict[str, Any] = {}
    for name, value in vars(args).items():
        result[name] = str(value) if isinstance(value, Path) else value
    return result


@dataclass(frozen=True)
class TraceItem:
    """One file record queued for the background trace writer."""

    stream: str
    event: dict[str, Any]


class TraceRun:
    """Create, collect, and finalize one owner-private demo timing trace."""

    def __init__(
        self,
        directory: Path,
        run_id: str,
        timebase_ns: int,
        manifest: dict[str, Any],
        *,
        queue_size: int = TRACE_QUEUE_SIZE,
    ) -> None:
        self.directory = directory
        self.run_id = run_id
        self.timebase_ns = timebase_ns
        self.manifest = manifest
        self._queue: queue.Queue[TraceItem | object] = queue.Queue(maxsize=queue_size)
        self._lock = threading.Lock()
        self._overflow_count = 0
        self._write_error: str | None = None
        self._closed = False
        self._segments: dict[str, dict[str, Any]] = {}
        self._phrases: dict[str, dict[str, Any]] = {}
        self._translations: dict[str, dict[str, Any]] = {}
        self._playback: dict[str, dict[str, Any]] = {}
        self._writer = threading.Thread(target=self._write_loop, name="timing-trace-writer")
        self._writer.start()

    @classmethod
    def create(
        cls,
        configuration: Mapping[str, Any],
        *,
        root: Path = TRACE_ROOT,
        now: datetime | None = None,
        timebase_ns: int | None = None,
        queue_size: int = TRACE_QUEUE_SIZE,
    ) -> "TraceRun":
        """Allocate the next private `YYYY_MM_DD_NNN` directory and manifest."""
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(root, 0o700)
        date = (now or datetime.now().astimezone()).strftime("%Y_%m_%d")
        directory: Path | None = None
        run_id = ""
        for sequence in range(1, 1_000_000):
            run_id = f"{date}_{sequence:03d}"
            candidate = root / run_id
            try:
                candidate.mkdir(mode=0o700)
            except FileExistsError:
                continue
            directory = candidate
            break
        if directory is None:
            raise RuntimeError(f"No available timing-trace run ID beneath {root}.")

        started_timebase = timebase_ns if timebase_ns is not None else time.monotonic_ns()
        manifest = {
            "schema_version": 1,
            "run_id": run_id,
            "status": "running",
            "trace_complete": True,
            "started_at": (now or datetime.now().astimezone()).isoformat(),
            "timebase_monotonic_ns": started_timebase,
            "timestamp_unit": "nanoseconds relative to timebase_monotonic_ns",
            "configuration": dict(configuration),
            "files": [
                "asr.ndjson",
                "phrases.ndjson",
                "translations.ndjson",
                "playback.ndjson",
                "timing.ndjson",
                "segments.ndjson",
            ],
            "trace_overflow_count": 0,
            "trace_write_error": None,
        }
        cls._write_json(directory / "manifest.json", manifest)
        return cls(directory, run_id, started_timebase, manifest, queue_size=queue_size)

    @staticmethod
    def _write_json(path: Path, value: Mapping[str, Any]) -> None:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
        os.chmod(path, 0o600)

    def now_ns(self) -> int:
        """Return a session-relative timestamp for a stage boundary."""
        return max(0, time.monotonic_ns() - self.timebase_ns)

    def stage(self, stream: str, event: Mapping[str, Any]) -> None:
        """Queue a complete stage event and its lightweight lifecycle record."""
        copied = dict(event)
        self._submit(TraceItem(stream, copied))
        trace = copied.get("timing")
        if not isinstance(trace, Mapping):
            return
        timestamps = trace.get("timestamps_ns", {})
        if not isinstance(timestamps, Mapping):
            return
        segment_id = trace.get("segment_id")
        phrase_id = trace.get("phrase_id")
        source_segment_ids = trace.get("source_segment_ids")
        for boundary, at_ns in timestamps.items():
            if boundary in TIMESTAMP_FIELDS or boundary.startswith("phrase_buffer_"):
                if isinstance(at_ns, int):
                    self.timing(
                        boundary,
                        segment_id=segment_id if isinstance(segment_id, str) else None,
                        phrase_id=phrase_id if isinstance(phrase_id, str) else None,
                        source_segment_ids=source_segment_ids if isinstance(source_segment_ids, list) else None,
                        queue_depths=trace.get("queue_depths") if isinstance(trace.get("queue_depths"), Mapping) else None,
                        at_ns=at_ns,
                    )

    def timing(
        self,
        boundary: str,
        *,
        segment_id: str | None = None,
        phrase_id: str | None = None,
        source_segment_ids: list[str] | None = None,
        queue_depth: int | None = None,
        logical_pending: int | None = None,
        queue_depths: Mapping[str, Any] | None = None,
        at_ns: int | None = None,
    ) -> None:
        """Queue one compact stage-boundary lifecycle event without file I/O."""
        self._submit(
            TraceItem(
                "timing",
                {
                    "run_id": self.run_id,
                    "boundary": boundary,
                    "at_monotonic_ns": self.now_ns() if at_ns is None else at_ns,
                    "segment_id": segment_id,
                    "phrase_id": phrase_id,
                    "source_segment_ids": source_segment_ids,
                    "queue_depth": queue_depth,
                    "logical_pending": logical_pending,
                    "queue_depths": dict(queue_depths) if queue_depths is not None else None,
                },
            )
        )

    def _submit(self, item: TraceItem) -> None:
        if self._closed:
            return
        try:
            self._queue.put_nowait(item)
        except queue.Full:
            with self._lock:
                self._overflow_count += 1

    def _write_loop(self) -> None:
        handles: dict[str, Any] = {}
        try:
            running = True
            while running:
                item = self._queue.get()
                batch: list[TraceItem | object] = [item]
                while len(batch) < 128:
                    try:
                        batch.append(self._queue.get_nowait())
                    except queue.Empty:
                        break
                for queued in batch:
                    if queued is _SENTINEL:
                        running = False
                        continue
                    assert isinstance(queued, TraceItem)
                    handle = handles.get(queued.stream)
                    if handle is None:
                        path = self.directory / f"{queued.stream}.ndjson"
                        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                        handle = os.fdopen(descriptor, "a", encoding="utf-8")
                        os.chmod(path, 0o600)
                        handles[queued.stream] = handle
                    handle.write(json.dumps(queued.event, ensure_ascii=False) + "\n")
                    self._ingest(queued.stream, queued.event)
                for handle in handles.values():
                    handle.flush()
        except Exception as error:
            with self._lock:
                self._write_error = str(error)
        finally:
            for handle in handles.values():
                handle.close()

    def _ingest(self, stream: str, event: Mapping[str, Any]) -> None:
        trace = event.get("timing")
        if not isinstance(trace, Mapping):
            return
        if stream == "asr":
            segment_id = trace.get("segment_id")
            if isinstance(segment_id, str):
                self._segments[segment_id] = dict(event)
        elif stream == "phrases":
            phrase_id = trace.get("phrase_id")
            if isinstance(phrase_id, str):
                self._phrases[phrase_id] = dict(event)
        elif stream == "translations":
            phrase_id = trace.get("phrase_id")
            if isinstance(phrase_id, str):
                self._translations[phrase_id] = dict(event)
        elif stream == "playback":
            phrase_id = trace.get("phrase_id")
            if isinstance(phrase_id, str):
                self._playback[phrase_id] = dict(event)

    def close(self, status: str) -> None:
        """Drain diagnostics outside the hot path and write terminal metrics."""
        if self._closed:
            return
        self._closed = True
        self._queue.put(_SENTINEL)
        self._writer.join(timeout=5)
        if self._writer.is_alive():
            with self._lock:
                self._write_error = self._write_error or "Trace writer did not stop within 5 seconds."
        try:
            self._write_segment_metrics(status)
        except OSError as error:
            with self._lock:
                self._write_error = self._write_error or str(error)
        with self._lock:
            self.manifest["trace_overflow_count"] = self._overflow_count
            self.manifest["trace_write_error"] = self._write_error
        self.manifest["trace_complete"] = not bool(
            self.manifest["trace_overflow_count"] or self.manifest["trace_write_error"]
        )
        self.manifest["status"] = status if self.manifest["trace_complete"] else "incomplete"
        self.manifest["ended_at"] = datetime.now().astimezone().isoformat()
        try:
            self._write_json(self.directory / "manifest.json", self.manifest)
        except OSError as error:
            with self._lock:
                self._write_error = self._write_error or str(error)

    def _write_segment_metrics(self, status: str) -> None:
        path = self.directory / "segments.ndjson"
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as output:
            for segment_id, source in self._segments.items():
                output.write(json.dumps(self._segment_metric(segment_id, source, status), ensure_ascii=False) + "\n")
        os.chmod(path, 0o600)

    def _segment_metric(
        self, segment_id: str, source: Mapping[str, Any], status: str
    ) -> dict[str, Any]:
        source_trace = source.get("timing", {})
        timestamps = empty_timestamps()
        if isinstance(source_trace, Mapping):
            timestamps.update(source_trace.get("timestamps_ns", {}))
        phrase = self._phrase_for_segment(segment_id)
        phrase_trace = phrase.get("timing", {}) if phrase else {}
        phrase_id = phrase_trace.get("phrase_id") if isinstance(phrase_trace, Mapping) else None
        translation = self._translations.get(phrase_id) if isinstance(phrase_id, str) else None
        playback = self._playback.get(phrase_id) if isinstance(phrase_id, str) else None
        queue_depths = dict(source_trace.get("queue_depths", {})) if isinstance(source_trace, Mapping) else {}
        for downstream in (phrase, translation, playback):
            trace = downstream.get("timing", {}) if downstream else {}
            if isinstance(trace, Mapping):
                timestamps.update({key: value for key, value in trace.get("timestamps_ns", {}).items() if value is not None})
                downstream_queues = trace.get("queue_depths", {})
                if isinstance(downstream_queues, Mapping):
                    queue_depths.update(downstream_queues)
        source_duration = milliseconds(timestamps["source_audio_start"], timestamps["source_audio_end"])
        derived = {
            "source_audio_duration_ms": source_duration,
            "vad_duration_ms": milliseconds(timestamps["vad_detected_start"], timestamps["vad_segment_closed"]),
            "asr_processing_duration_ms": milliseconds(timestamps["asr_start"], timestamps["asr_complete"]),
            "translation_processing_duration_ms": milliseconds(timestamps["translation_start"], timestamps["translation_complete"]),
            "tts_processing_duration_ms": milliseconds(timestamps["tts_start"], timestamps["tts_complete"]),
            "time_to_first_tts_audio_ms": milliseconds(timestamps["tts_start"], timestamps["tts_first_audio"]),
            "playback_duration_ms": milliseconds(timestamps["playback_start"], timestamps["playback_complete"]),
            "wait_before_asr_ms": milliseconds(
                timestamps["vad_segment_closed"] or timestamps["source_audio_end"], timestamps["asr_start"]
            ),
            "wait_before_translation_ms": milliseconds(
                timestamps.get("phrase_buffer_released"), timestamps["translation_start"]
            ),
            "wait_before_tts_ms": milliseconds(timestamps["translation_complete"], timestamps["tts_start"]),
            "wait_before_playback_ms": milliseconds(timestamps["tts_first_audio"], timestamps["playback_start"]),
            "end_to_end_playback_start_ms": milliseconds(timestamps["source_audio_end"], timestamps["playback_start"]),
            "end_to_end_playback_complete_ms": milliseconds(timestamps["source_audio_end"], timestamps["playback_complete"]),
        }
        for name, start, end in (
            ("asr_rtf", timestamps["asr_start"], timestamps["asr_complete"]),
            ("tts_rtf", timestamps["tts_start"], timestamps["tts_complete"]),
        ):
            duration = milliseconds(start, end)
            derived[name] = duration / source_duration if duration is not None and source_duration else None
        completion = (
            "completed"
            if timestamps["playback_complete"] is not None
            else "interrupted" if status == "interrupted" else "incomplete"
        )
        return {
            "run_id": self.run_id,
            "segment_id": segment_id,
            "phrase_id": phrase_id,
            "source_segment_ids": phrase_trace.get("source_segment_ids", [segment_id]) if isinstance(phrase_trace, Mapping) else [segment_id],
            "source_start_ms": source.get("start_ms"),
            "source_end_ms": source.get("end_ms"),
            "timestamps_ns": timestamps,
            "queue_depths": queue_depths,
            "derived_metrics": derived,
            "completion_state": completion,
        }

    def _phrase_for_segment(self, segment_id: str) -> dict[str, Any] | None:
        for phrase in self._phrases.values():
            trace = phrase.get("timing", {})
            if isinstance(trace, Mapping) and segment_id in trace.get("source_segment_ids", []):
                return phrase
        return None

    @property
    def diagnostic_error(self) -> str | None:
        """Return a trace failure suitable for one operator-facing diagnostic."""
        with self._lock:
            return self._write_error
