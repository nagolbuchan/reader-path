"""Per-run CrewAI logs: verbose trace, task outputs, and final course JSON."""

from __future__ import annotations

import io
import json
import sys
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

# backend/logs/crew/<run_id>/
_LOG_ROOT = Path(__file__).resolve().parents[2] / "logs" / "crew"
_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_run_dir(run_id: str) -> Path:
    path = _LOG_ROOT / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def crew_tasks_log_path(run_id: str) -> Path:
    return ensure_run_dir(run_id) / "crew_tasks.json"


def run_manifest_path(run_id: str) -> Path:
    return ensure_run_dir(run_id) / "run.json"


def final_course_path(run_id: str) -> Path:
    return ensure_run_dir(run_id) / "final_course.json"


def verbose_trace_path(run_id: str) -> Path:
    return ensure_run_dir(run_id) / "verbose.txt"


class _TeeStream:
    def __init__(self, *streams: Any) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            try:
                stream.write(data)
            except UnicodeEncodeError:
                # Windows consoles may still be charmap; drop unsupported glyphs.
                try:
                    encoding = getattr(stream, "encoding", None) or "utf-8"
                    safe = data.encode(encoding, errors="replace").decode(
                        encoding, errors="replace"
                    )
                    stream.write(safe)
                except Exception:
                    pass
            except Exception:
                pass
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            try:
                stream.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        return False

    @property
    def encoding(self) -> str:
        return "utf-8"


@contextmanager
def capture_verbose_trace(run_id: str) -> Iterator[io.StringIO]:
    """Tee stdout/stderr into memory + verbose.txt while CrewAI runs."""
    buf = io.StringIO()
    file_path = verbose_trace_path(run_id)
    file_handle = open(file_path, "a", encoding="utf-8")
    tee_out = _TeeStream(sys.__stdout__, buf, file_handle)
    tee_err = _TeeStream(sys.__stderr__, buf, file_handle)
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = tee_out  # type: ignore[assignment]
    sys.stderr = tee_err  # type: ignore[assignment]
    try:
        yield buf
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        file_handle.close()


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


class CrewRunLogger:
    """Accumulates one generation run and writes run.json + final_course.json."""

    def __init__(self, run_id: str, topic: str) -> None:
        self.run_id = run_id
        self.topic = topic
        self.started_at = _utc_now()
        self.finished_at: Optional[str] = None
        self.status: str = "running"
        self.category: Optional[str] = None
        self.verbose_trace: str = ""
        self.agent_steps: List[Any] = []
        self.agent_raw_output: Optional[str] = None
        self.course_from_agents: Optional[dict] = None
        self.repairs: List[str] = []
        self.final_course: Optional[dict] = None
        self.error: Optional[str] = None
        ensure_run_dir(run_id)

    @property
    def dir_path(self) -> Path:
        return ensure_run_dir(self.run_id)

    def append_step(self, step: Any) -> None:
        self.agent_steps.append(_jsonable(step))

    def load_crew_tasks(self) -> List[Any]:
        path = crew_tasks_log_path(self.run_id)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else [data]
        except (json.JSONDecodeError, OSError):
            return []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "topic": self.topic,
            "category": self.category,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "files": {
                "run": str(run_manifest_path(self.run_id)),
                "crew_tasks": str(crew_tasks_log_path(self.run_id)),
                "verbose": str(verbose_trace_path(self.run_id)),
                "final_course": str(final_course_path(self.run_id)),
            },
            "verbose_trace": self.verbose_trace,
            "agent_steps": self.agent_steps,
            "crew_tasks": self.load_crew_tasks(),
            "agent_raw_output": self.agent_raw_output,
            "course_from_agents": self.course_from_agents,
            "repairs": self.repairs,
            "final_course": self.final_course,
            "error": self.error,
        }

    def write(self) -> Path:
        self.finished_at = self.finished_at or _utc_now()
        payload = self.to_dict()
        manifest = run_manifest_path(self.run_id)
        with _lock:
            manifest.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            if self.final_course is not None:
                final_course_path(self.run_id).write_text(
                    json.dumps(self.final_course, indent=2, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
        return manifest


def read_run_log(run_id: str) -> Optional[dict]:
    path = run_manifest_path(run_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
