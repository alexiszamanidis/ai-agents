---
name: agent-context-cleanup
description: >-
    Audits local AI-agent rules, skills, hooks, MCP configuration, caches, and
    stores for recurring token overhead, duplication, stale files, and exposed
    secret configuration. Use only when explicitly invoked for agent-context
    maintenance or cleanup.
disable-model-invocation: true
---

# Agent context cleanup

Audit first. Never delete or rewrite configuration merely because it is large.

## Run the audit

Execute the script beside this file:

```bash
python3 "<skill-dir>/scripts/audit_agent_context.py" \
  --workspace "${CURSOR_PROJECT_DIR:-$PWD}"
```

Use `--json` when structured output is useful.

## Interpret cost correctly

-   Always-applied rules and auto-invoked skill descriptions can affect each request.
-   Skill bodies are normally loaded only when invoked.
-   Hook scripts cost no model tokens unless they inject context or trigger another generation.
-   MCP tool names may be advertised routinely, while full schemas are loaded on demand.
-   Chats, caches, agent stores, and disabled skill bodies primarily consume disk.
-   Symlink aliases are not duplicate disk usage, but multiple discovery locations can still duplicate context.

## Cleanup workflow

1. Confirm each duplicate by resolved path and normalized content.
2. Check recent usage before disabling or removing a skill or MCP server.
3. Prefer `disable-model-invocation: true` for useful but rarely automatic skills.
4. Keep one canonical always-applied rule. Preserve tool-specific copies only when that tool requires them.
5. Remove stale caches only through the owning application's documented mechanism.
6. Never delete Cursor-managed skills, active chats, agent stores, or credentials automatically.
7. If a config contains plaintext credentials, report only variable names. Recommend rotation and environment-based secret injection.
8. Present an exact change plan and obtain confirmation before deleting personal configuration outside a repository.

After approved changes, rerun the audit and compare recurring context estimates. Report recurring context separately from disk reclaimed.
