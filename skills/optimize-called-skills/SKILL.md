---
name: optimize-called-skills
description: >-
  Audits skills in this repository against their real agent-transcript runs
  and tightens instructions or scripts where those runs wasted steps or failed.
  Use when the user asks to optimize, tune, or improve the skills that were
  called, or invokes optimize-called-skills.
disable-model-invocation: true
---

# Optimize called skills

Audit `skills/*/SKILL.md` in this repository. Change a skill only when one of its real runs shows wasted or fragile work.

## Find calls

1. List every `skills/*/SKILL.md`.
2. Search this workspace's Cursor agent transcripts for `Skill Name: <name>`, `/<name>`, or that skill's path.
3. Ignore chats that only create or edit the skill.
4. Leave a skill with no invocation unchanged, and say that it had no execution evidence.

## Read the runs

For each called skill, keep only repeated or failed work:

- schema lookups that belong in one parallel batch
- independent reads made serially
- a follow-up fetch after create or update already returned the key
- broader searches after a distinctive identifier already explained the request
- generated one-off code for a lookup the skill repeats
- credentials parsed from MCP config
- message text passed through shell quotes
- the wrong MCP namespace for a known issue key
- success reported after a partial script failure
- unbounded result or report size

## Change

Keep approval gates, field values, templates, and domain rules already in the skill. Do not restore a fallback the user removed.

Prefer one short instruction, or a deterministic script for a fragile repeated lookup. Keep `SKILL.md` concise.

## Check

Compile changed Python. Test new script behavior with a mock or its failure path, without calling a live service. Run `git diff --check`. Do not commit unless asked.

## Reply

For every skill, say whether it was called. For each change, name the wasted run step and the file changed.
