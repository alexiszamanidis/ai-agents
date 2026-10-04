# ai-agents

This repository contains curated agent skill definitions for AI-assisted development workflows.

## Structure

-   `skills/chat-history-skill-audit/`: Find repeated workflows across local Cursor chats and compare them with existing skills.
-   `skills/agent-context-cleanup/`: Audit recurring agent context, duplicate configuration, plaintext secret fields, and disk-only state.
-   `skills/clean-code/`: Clean Code guidance and rules.
-   `skills/commit/`: Review changes and commit using branch-derived messages: `PROJ-1234: summary` on ticket branches, or `feat(scope): summary` otherwise.
-   `skills/optimize-called-skills/`: Improve skills using evidence from their real transcript runs.
-   `skills/refactoring/`: Refactoring practices and recommendations.
-   `skills/working-effectively-with-legacy-code/`: Legacy code handling and maintenance guidance.

## Purpose

Use these skill files as prompts or reference material for code review, refactoring, and improving maintainability.

## Notes

Each skill folder contains a `SKILL.md` prompt definition that captures the behavior and constraints for a particular development mindset.

## Install

`./install` links this repository into the Cursor user config. `./unlink` removes only links that point back into this repository.

-   Skills link into `~/.agents/skills`.
-   `.cursor/rules/global-agent-instructions.mdc` links into `~/.cursor/rules`.
-   `.cursor/hooks/hooks.json` links to `~/.cursor/hooks.json`.
-   `.cursor/hooks/monthly-context-cleanup.py` links into `~/.cursor/hooks`.

## Useful links

-   [agent-rules-books](https://github.com/ciembor/agent-rules-books/)
