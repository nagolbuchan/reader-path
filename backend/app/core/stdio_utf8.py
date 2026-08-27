"""Make Windows consoles accept CrewAI emoji / Unicode log output."""

from __future__ import annotations

import os
import sys


def configure_utf8_stdio() -> None:
    """
    Force UTF-8 on stdout/stderr so CrewAI event logs (✨, 📋, …) do not crash
    on Windows cp1252/charmap consoles.
    """
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
                continue
            except Exception:
                pass

        buffer = getattr(stream, "buffer", None)
        if buffer is None:
            continue
        try:
            import io

            wrapped = io.TextIOWrapper(
                buffer,
                encoding="utf-8",
                errors="replace",
                line_buffering=True,
            )
            setattr(sys, name, wrapped)
        except Exception:
            pass
