#!/usr/bin/env python3
"""Audit local AI-agent configuration without exposing secret values."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SECRET_KEY = re.compile(r"(token|secret|password|api[_-]?key|credential)", re.I)
FRONTMATTER = re.compile(r"\A---\s*\n.*?\n---\s*\n?", re.S)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}

    result: dict[str, str] = {}
    lines = text[4:end].splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if value in {">", ">-", "|", "|-"}:
            chunks: list[str] = []
            index += 1
            while index < len(lines) and (
                not lines[index].strip() or lines[index].startswith((" ", "\t"))
            ):
                chunks.append(lines[index].strip())
                index += 1
            result[key] = " ".join(chunk for chunk in chunks if chunk)
            continue
        value = re.sub(r"\s+#.*$", "", value).strip()
        result[key] = value.strip("\"'")
        index += 1
    return result


def normalize_instructions(text: str) -> str:
    text = FRONTMATTER.sub("", text)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        stripped = re.sub(r"^[-*]\s+", "", stripped)
        lines.append(re.sub(r"\s+", " ", stripped).lower())
    return "\n".join(lines)


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def existing(paths: list[Path]) -> list[Path]:
    return [path for path in paths if path.exists()]


def discover_skills(home: Path, workspace: Path) -> list[dict[str, Any]]:
    roots = [
        ("cursor-user", home / ".cursor" / "skills"),
        ("agents-user", home / ".agents" / "skills"),
        ("workspace-cursor", workspace / ".cursor" / "skills"),
        ("workspace", workspace / "skills"),
    ]
    skills: list[dict[str, Any]] = []
    for scope, root in roots:
        if not root.is_dir():
            continue
        try:
            paths = sorted(root.glob("*/SKILL.md"))
        except OSError:
            continue
        for path in paths:
            text = read_text(path)
            metadata = parse_frontmatter(text)
            description = metadata.get("description", "")
            disabled = metadata.get("disable-model-invocation", "").lower() == "true"
            try:
                resolved = str(path.resolve())
            except OSError:
                resolved = str(path)
            skills.append(
                {
                    "name": metadata.get("name") or path.parent.name,
                    "path": str(path),
                    "resolved_path": resolved,
                    "scope": scope,
                    "bytes": len(text.encode("utf-8")),
                    "description_chars": len(description),
                    "automatic": bool(description) and not disabled,
                }
            )
    return skills


def discover_rules(home: Path, workspace: Path) -> list[dict[str, Any]]:
    paths = [
        home / ".cursor" / "rules" / "global-agent-instructions.mdc",
        workspace / ".cursor" / "rules" / "global-agent-instructions.mdc",
        workspace / "AGENTS.md",
        home / ".github" / "copilot-instructions.md",
        home / ".claude" / "CLAUDE.md",
    ]
    rules = []
    for path in existing(paths):
        text = read_text(path)
        normalized = normalize_instructions(text)
        try:
            resolved = str(path.resolve())
        except OSError:
            resolved = str(path)
        rules.append(
            {
                "path": str(path),
                "resolved_path": resolved,
                "bytes": len(text.encode("utf-8")),
                "normalized_hash": short_hash(normalized),
                "estimated_tokens": round(len(text) / 4),
            }
        )
    return rules


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def discover_hooks(home: Path, workspace: Path) -> list[dict[str, Any]]:
    paths = [
        home / ".cursor" / "hooks.json",
        workspace / ".cursor" / "hooks.json",
        workspace / ".cursor" / "hooks" / "hooks.json",
    ]
    results = []
    for path in existing(paths):
        data = load_json(path)
        hooks = data.get("hooks", {})
        events = {
            event: len(entries) if isinstance(entries, list) else 0
            for event, entries in hooks.items()
        } if isinstance(hooks, dict) else {}
        results.append({"path": str(path), "events": events})
    return results


def secret_names(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            field = f"{prefix}.{key}" if prefix else str(key)
            if SECRET_KEY.search(str(key)) and child not in (None, ""):
                found.append(field)
            else:
                found.extend(secret_names(child, field))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(secret_names(child, f"{prefix}[{index}]"))
    return found


def discover_mcp(home: Path, workspace: Path) -> list[dict[str, Any]]:
    paths = [
        home / ".cursor" / "mcp.json",
        workspace / ".cursor" / "mcp.json",
        home / ".claude" / "mcp.json",
    ]
    results = []
    for path in existing(paths):
        data = load_json(path)
        servers = data.get("mcpServers", {})
        results.append(
            {
                "path": str(path),
                "servers": sorted(servers) if isinstance(servers, dict) else [],
                "plaintext_secret_fields": sorted(secret_names(data)),
            }
        )
    return results


def tree_size(path: Path) -> int:
    total = 0
    if not path.exists():
        return total
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def build_report(home: Path, workspace: Path) -> dict[str, Any]:
    skills = discover_skills(home, workspace)
    rules = discover_rules(home, workspace)
    hooks = discover_hooks(home, workspace)
    mcp = discover_mcp(home, workspace)

    aliases: dict[str, list[str]] = defaultdict(list)
    for skill in skills:
        aliases[skill["resolved_path"]].append(skill["path"])

    duplicate_rules: dict[str, list[str]] = defaultdict(list)
    for rule in rules:
        duplicate_rules[rule["normalized_hash"]].append(rule["path"])

    automatic_description_chars = sum(
        skill["description_chars"] for skill in skills if skill["automatic"]
    )
    disk_paths = [
        home / ".cursor" / "chats",
        home / ".cursor" / "projects",
        home / ".local" / "state" / "cursor" / "agent-stores",
    ]

    return {
        "workspace": str(workspace),
        "recurring_context_estimate": {
            "automatic_skill_description_chars": automatic_description_chars,
            "automatic_skill_description_tokens": round(
                automatic_description_chars / 4
            ),
            "rule_tokens_if_all_listed_rules_apply": sum(
                rule["estimated_tokens"] for rule in rules
            ),
            "note": "Estimates are directional. Product-managed context may differ by tool and workspace.",
        },
        "skills": skills,
        "skill_alias_groups": [
            paths for paths in aliases.values() if len(paths) > 1
        ],
        "rules": rules,
        "duplicate_rule_groups": [
            paths for paths in duplicate_rules.values() if len(paths) > 1
        ],
        "hooks": hooks,
        "mcp": mcp,
        "disk_only_bytes": {
            str(path): tree_size(path) for path in disk_paths if path.exists()
        },
        "recommendations": [
            "Remove duplicate always-applied instructions from overlapping discovery locations.",
            "Disable automatic invocation for useful skills that should only run explicitly.",
            "Remove unused MCP servers only after checking recent workflows.",
            "Rotate plaintext credentials and inject them through environment-based secret storage.",
            "Do not delete app-managed skills, chats, caches, or agent stores solely to reduce tokens.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    estimate = report["recurring_context_estimate"]
    print("Agent context audit")
    print(f"Workspace: {report['workspace']}")
    print(
        "Automatic skill descriptions: "
        f"~{estimate['automatic_skill_description_tokens']} tokens"
    )
    print(
        "Listed rules if all apply: "
        f"~{estimate['rule_tokens_if_all_listed_rules_apply']} tokens"
    )

    print("\nDuplicate instruction groups:")
    groups = report["duplicate_rule_groups"]
    if not groups:
        print("- none")
    for paths in groups:
        print("- " + " | ".join(paths))

    print("\nSkill aliases:")
    aliases = report["skill_alias_groups"]
    if not aliases:
        print("- none")
    for paths in aliases:
        print("- " + " | ".join(paths))

    print("\nAutomatic skills:")
    automatic = [skill for skill in report["skills"] if skill["automatic"]]
    if not automatic:
        print("- none")
    for skill in automatic:
        tokens = round(skill["description_chars"] / 4)
        print(f"- {skill['name']}: ~{tokens} description tokens ({skill['path']})")

    print("\nHooks:")
    if not report["hooks"]:
        print("- none")
    for hook in report["hooks"]:
        print(f"- {hook['path']}: {hook['events']}")

    print("\nMCP servers and plaintext secret fields:")
    if not report["mcp"]:
        print("- none")
    for config in report["mcp"]:
        print(f"- {config['path']}: {', '.join(config['servers']) or 'no servers'}")
        for field in config["plaintext_secret_fields"]:
            print(f"  SECRET FIELD: {field}")

    print("\nDisk-only locations:")
    for path, size in report["disk_only_bytes"].items():
        print(f"- {path}: {size / (1024 * 1024):.1f} MiB")

    print("\nRecommendations:")
    for recommendation in report["recommendations"]:
        print(f"- {recommendation}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_report(Path.home(), args.workspace.expanduser().resolve())
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
