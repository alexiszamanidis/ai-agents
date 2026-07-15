---
name: commit
description: >
    Review local git changes and commit with a message derived from the branch
    name. Use when the user asks to commit, says /commit, or asks to
    "commit my changes".
disable-model-invocation: true
---

# Commit

Only commit when the user explicitly asks.

## Workflow

1. Review the changes with `git status`, `git diff`, and `git diff --staged`.
2. Check the branch name with `git branch --show-current`.
3. Choose a commit message:
   - Ticket branch: `[ticket-symbol]-[ticket-number]: concise imperative summary`
   - Non-ticket branch: `type(scope): short summary`
4. Show the branch, files to stage, and the proposed message. Wait for approval unless the user already asked to commit.
5. Stage only relevant paths and commit with a HEREDOC. Run `git status` after.

## Safety

- Do not commit secrets, `.env`, logs, or unrelated files.
- Do not use `--no-verify`, `--force`, `push --force`, or `reset --hard` unless explicitly requested.
- Do not amend or push unless explicitly requested.
- Do not create empty commits.
