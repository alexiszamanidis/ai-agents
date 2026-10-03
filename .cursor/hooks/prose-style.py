#!/usr/bin/env python3
"""Ask for a rewrite when a reply uses typographic dashes or a comma before and."""

import json
import re
import sys
from pathlib import Path

STATE_DIR = Path.home() / ".cursor" / "hooks" / "state"

# Typographic dashes. ASCII hyphen-minus (-) is allowed.
DASHES = {
    "\u2010": "hyphen",
    "\u2011": "non-breaking hyphen",
    "\u2012": "figure dash",
    "\u2013": "en dash",
    "\u2014": "em dash",
    "\u2015": "horizontal bar",
    "\u2212": "minus sign",
}

COMMA_BEFORE_AND = re.compile(r",\s*and\b", re.IGNORECASE)
FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)


def load_input():
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def emit(payload):
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def state_path(data):
    conversation_id = data.get("conversation_id") or "unknown"
    generation_id = data.get("generation_id") or "unknown"
    safe_conversation = conversation_id.replace("/", "_")
    safe_generation = generation_id.replace("/", "_")
    return STATE_DIR / f"{safe_conversation}--{safe_generation}.json"


def found_dashes(text):
    present = []
    for char, name in DASHES.items():
        if char in text and name not in present:
            present.append(name)
    return present


def prose_text(text):
    return FENCED_CODE.sub("", text)


def has_comma_before_and(text):
    return COMMA_BEFORE_AND.search(prose_text(text)) is not None


def followup_message(dashes, comma_before_and):
    parts = []
    if dashes:
        names = ", ".join(dashes)
        parts.append(
            f"Your previous reply used {names}. "
            "Rewrite that reply so it contains none of those characters. "
            "Use periods, parentheses, or a plain ASCII hyphen (-) "
            "when a hyphen is required in a word, path, or flag."
        )
    if comma_before_and:
        parts.append(
            "Your previous reply used a comma before and. "
            "Rewrite that reply and remove every comma that comes immediately before and. "
            "For example, write 'red, white and blue'."
        )
    return " ".join(parts)


def handle_response(data):
    text = data.get("text") or ""
    path = state_path(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "dashes": found_dashes(text),
                "comma_before_and": has_comma_before_and(text),
            }
        ),
        encoding="utf-8",
    )
    emit({})


def handle_stop(data):
    path = state_path(data)
    if data.get("status") != "completed":
        path.unlink(missing_ok=True)
        emit({})
        return

    if not path.exists():
        emit({})
        return

    try:
        saved = json.loads(path.read_text(encoding="utf-8"))
    finally:
        path.unlink(missing_ok=True)

    dashes = saved.get("dashes") or []
    comma_before_and = bool(saved.get("comma_before_and"))
    if not dashes and not comma_before_and:
        emit({})
        return

    emit({"followup_message": followup_message(dashes, comma_before_and)})


def main():
    try:
        data = load_input()
    except json.JSONDecodeError:
        emit({})
        return 0

    event = data.get("hook_event_name")
    if event == "afterAgentResponse":
        handle_response(data)
    elif event == "stop":
        handle_stop(data)
    else:
        emit({})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
