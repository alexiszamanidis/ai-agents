---
name: commit
description: >
    Review local git changes and commit with a message derived from the branch
    name. Use when the user asks to commit, says /commit, or asks to
    "commit my changes".
disable-model-invocation: true
---

# Ticket Commit

Only commit when the user explicitly asks.

## Workflow

1. Run in parallel: `git status`, `git diff`, `git diff --staged`, `git branch --show-current`, `git log -5 --oneline`
2. Summarize changes. Do not commit secrets, `.env`, logs, or unrelated files.
3. Pick the commit format from the current branch name (see below).
4. Show branch, files to stage, and proposed message. Wait for approval unless the user already said to commit.
5. Stage only relevant paths (not `git add -A` / `git add .` by default). Commit with a HEREDOC. Run `git status` after.

## Commit message format

### Ticket branch

If the branch matches `[ticket-symbol]-[ticket-number]-[branch-name]` (e.g. `PROJ-1234-fix-metrics`):

```text
[ticket-symbol]-[ticket-number]: concise imperative summary
```

Example: `PROJ-1234: tighten metrics retention window`

### Non-ticket branch

Otherwise:

```text
feat(tool1,tool2): concise mes1, concise mes2
```

-   `feat` is the default type; use `fix`, `docs`, `refactor`, etc. when it fits better.
-   Scope is one or more tools/areas, comma-separated.
-   Body is short imperative phrases, comma-separated when there are multiple changes.

Example: `feat(i3,nvim): fix i3 window, add nvim lsp config`

## Safety

-   Never update git config
-   Never use `--no-verify`, `--force`, `push --force`, or `reset --hard` unless explicitly requested
-   Never amend unless the user asked, it is your unpushed commit, and amend rules apply
-   Never push unless explicitly requested
-   Never create empty commits
