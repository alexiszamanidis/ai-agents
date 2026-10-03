#!/usr/bin/env python3
"""Inject a lightweight agent-context cleanup reminder every 30 days."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

INTERVAL_SECONDS = 30 * 24 * 60 * 60
DEFAULT_STATE_FILE = (
    Path.home() / ".cursor" / "hooks" / "state" / "context-cleanup-reminder.json"
)
REMINDER = (
    "Monthly agent-context maintenance is due. Briefly remind the user that "
    "they can invoke /agent-context-cleanup to audit rules, skills, hooks, MCP "
    "configuration, caches, stores, duplication and recurring token overhead. "
    "Do not run cleanup automatically."
)


def emit(payload: dict[str, object]) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def now() -> float:
    override = os.environ.get("AGENT_CONTEXT_CLEANUP_NOW")
    return float(override) if override else time.time()


def state_file() -> Path:
    override = os.environ.get("AGENT_CONTEXT_CLEANUP_STATE_FILE")
    return Path(override).expanduser() if override else DEFAULT_STATE_FILE


def last_reminder(path: Path) -> float:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return float(data.get("last_reminder", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_reminder(path: Path, timestamp: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"last_reminder": timestamp}) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
        if data.get("hook_event_name") != "sessionStart":
            emit({})
            return 0

        timestamp = now()
        path = state_file()
        if timestamp - last_reminder(path) < INTERVAL_SECONDS:
            emit({})
            return 0

        save_reminder(path, timestamp)
        emit({"additional_context": REMINDER})
    except Exception:
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
