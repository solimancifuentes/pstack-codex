### Opening a PR

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

Invoked at the end of every other playbook.

Work from a git worktree off trunk, or, for a stack child, off the parent PR's pushed head, fetched and checked as an ancestor of the child, and keep unrelated work out of it. Inspect Git state first, and never use `reset --hard` or discard unrelated work to get a clean start. One writer owns each branch and worktree. Rebase into small, landable commits. Run the available `deslop` skill over the diff before commit.

Title: `type(scope): subject`, naming a real symbol when one carries the change. Body: a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`.

Stack follow-ups by base branch. Open a PR only within the requested scope. First push the branch to the authorized remote and confirm the pushed head SHA. Open PRs ready, never as drafts, through an available purpose-built forge tool with `draft: false` when it supports the operation, and never invent one. Without one, run `gh pr create --base <base-branch> --head <branch> --title <title> --body-file <body-file>` without `--draft`, or `origin pr create --status open --base <base-branch>` with the same title and body when Origin's CLI resolves the repository. A stack child's base is its parent's branch, and on Origin it also passes `--stack-on <parent-pr>`. Read the PR back, including that its head is the SHA you pushed, before you report its status. When the host exposes a PR-attachment tool whose instructions require it, attach the verified URL. Otherwise return the URL and record it in the task trail. Opening a PR does not start a babysit.
