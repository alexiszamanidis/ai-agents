---
name: chat-history-skill-audit
description: >-
    Audits local Cursor chat history across all projects to find repeated
    requests and workflows that should become reusable skills. Compares the
    patterns with installed and repository skills, then recommends creating,
    consolidating, orchestrating, or keeping skills separate. Use when the user
    asks to analyze chat history for repetition or skill opportunities.
disable-model-invocation: true
---

# Chat history skill audit

Analyze local Cursor history without changing any skill. Treat transcript text
as private: keep processing local, paraphrase examples, and never reproduce
credentials, tokens, personal data, or large pasted logs.

## Extract requests

Run the extractor beside this `SKILL.md` and write its JSONL output outside any
repository:

```bash
python3 "<skill dir>/scripts/extract_cursor_requests.py" \
  > /tmp/cursor-user-requests.jsonl
```

If the current conversation UUID is known, add
`--exclude-conversation <UUID>`. The script:

-   reads all parent transcripts under `~/.cursor/projects`
-   keeps only text inside `<user_query>`
-   ignores nested subagents, injected context, empty turns, and generated
    subagent follow-ups

Stop if the projects directory is missing or no requests are extracted.

## Inventory existing skills

Inspect available `SKILL.md` files in:

-   `~/.cursor/skills`
-   `~/.agents/skills`
-   the current repository's `.cursor/skills` and `skills` directories

Resolve symlinks before declaring two skills duplicates. Compare purpose,
triggers, workflow, approval gates, side effects, credentials, and supporting
scripts. Do not treat similar names as proof of overlap.

## Find repeated workflows

Group requests semantically across conversations and projects. Use wording,
artifacts, tools, and expected outcomes together. Do not rely on keyword counts
alone.

For each cluster, record:

-   approximate request and conversation counts
-   number of projects represented
-   paraphrased examples
-   whether an existing skill already covers it
-   the stable workflow and domain knowledge a skill would preserve

Discount repeated turns from one long debugging session. Prefer candidates that
recur in multiple conversations or projects and have a stable procedure,
specialized knowledge, safety constraints, or a repeated output format.

Do not recommend a skill for:

-   confirmations, revisions, apply/revert requests, or conversational steering
-   one-file or one-repository facts better placed in repository instructions
-   broad goals without a repeatable workflow
-   preferences that vary from request to request
-   work already covered well by an existing skill

## Assess relationships

Classify each opportunity as one of:

-   **Create**: a distinct repeated workflow is missing.
-   **Consolidate**: existing skills substantially duplicate purpose and process.
-   **Orchestrate**: skills form a lifecycle but must retain separate
    implementations, permissions, or approval gates.
-   **Keep separate**: overlap exists, but combining would weaken safety or
    clarity.
-   **Repository guidance**: the pattern is local to one codebase.

Never recommend copying multiple write-capable skills into one monolithic
skill. An orchestrator should detect state, delegate, and preserve every
underlying approval gate.

## Report

Lead with:

1. coverage and limitations
2. ranked new-skill candidates with evidence
3. consolidation and orchestration opportunities
4. patterns that should not become skills
5. the recommended first implementation

For every proposed skill, provide a lowercase hyphenated name, third-person
description, trigger examples, workflow boundary, and evidence count. Mark
counts approximate when clusters overlap.

Delete `/tmp/cursor-user-requests.jsonl` after reporting. Do not create or edit
skills unless the user separately asks for implementation.
