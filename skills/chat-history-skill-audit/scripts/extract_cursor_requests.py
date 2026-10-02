#!/usr/bin/env python3
"""Extract genuine user requests from parent Cursor agent transcripts."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator

USER_QUERY = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.DOTALL)
TIMESTAMP = re.compile(r"<timestamp>\s*(.*?)\s*</timestamp>", re.DOTALL)
FOLLOWUP_PREFIX = "Briefly inform the user about the task result"


def parent_transcripts(projects_root: Path) -> Iterator[Path]:
    """Yield parent transcripts, excluding nested subagent transcripts."""
    for path in sorted(projects_root.glob("*/agent-transcripts/*/*.jsonl")):
        if path.stem == path.parent.name:
            yield path


def text_content(record: object) -> str:
    if not isinstance(record, dict) or record.get("role") != "user":
        return ""

    message = record.get("message")
    if not isinstance(message, dict):
        return ""

    content = message.get("content")
    if not isinstance(content, list):
        return ""

    return "\n".join(
        item.get("text", "")
        for item in content
        if isinstance(item, dict)
        and item.get("type") == "text"
        and isinstance(item.get("text"), str)
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract user requests from local Cursor transcripts as JSONL."
    )
    parser.add_argument(
        "--projects-root",
        type=Path,
        default=Path.home() / ".cursor" / "projects",
        help="Cursor projects directory (default: ~/.cursor/projects).",
    )
    parser.add_argument(
        "--exclude-conversation",
        action="append",
        default=[],
        metavar="UUID",
        help="Conversation UUID to exclude. May be supplied more than once.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    projects_root = args.projects_root.expanduser().resolve()
    excluded = set(args.exclude_conversation)

    if not projects_root.is_dir():
        print(
            f"Cursor projects directory does not exist: {projects_root}",
            file=sys.stderr,
        )
        return 2

    malformed_lines = 0
    emitted = 0

    for path in parent_transcripts(projects_root):
        conversation_id = path.parent.name
        if conversation_id in excluded:
            continue

        project = path.parents[2].name
        request_index = 0

        with path.open(encoding="utf-8", errors="replace") as transcript:
            for line in transcript:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    malformed_lines += 1
                    continue

                envelope = text_content(record)
                query_match = USER_QUERY.search(envelope)
                if query_match is None:
                    continue

                request = query_match.group(1).strip()
                if not request or request.startswith(FOLLOWUP_PREFIX):
                    continue

                timestamp_match = TIMESTAMP.search(envelope)
                result = {
                    "project": project,
                    "conversation_id": conversation_id,
                    "path": str(path),
                    "request_index": request_index,
                    "timestamp": (
                        timestamp_match.group(1).strip()
                        if timestamp_match is not None
                        else None
                    ),
                    "text": request,
                }
                print(json.dumps(result, ensure_ascii=False))
                request_index += 1
                emitted += 1

    print(
        f"Extracted {emitted} requests; skipped {malformed_lines} malformed lines.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
