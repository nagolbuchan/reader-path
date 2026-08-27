"""In-memory + on-disk cache of unused verified books for quick reading replacement."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, List, Optional

from app.models.course import BookReading
from app.services.crew_run_log import ensure_run_dir

_lock = threading.Lock()
_cache: Dict[str, List[dict]] = {}


def replacement_pool_path(run_id: str) -> Path:
    return ensure_run_dir(run_id) / "replacement_pool.json"


def set_replacement_pool(run_id: str, readings: List[BookReading]) -> Path:
    payload = [r.model_dump() for r in readings]
    path = replacement_pool_path(run_id)
    with _lock:
        _cache[run_id] = payload
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(f"Cached {len(payload)} unused book(s) for replacement: {path}")
    return path


def get_replacement_pool(run_id: str) -> Optional[List[dict]]:
    with _lock:
        if run_id in _cache:
            return list(_cache[run_id])

    path = replacement_pool_path(run_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, list):
        return None
    with _lock:
        _cache[run_id] = data
    return list(data)
