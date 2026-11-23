### Opening a PR

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

Invoked at the end of every other playbook.

Work from a git worktree off the PR's actual base, and keep unrelated work out of it. That is trunk for independent work, and the parent branch's verified tip for a stack child. Inspect Git state first, and never use `reset --hard` or discard unrelated work to get a clean start. One writer owns each branch and worktree. Rebase into small, landable commits. Run the available `deslop` skill over the diff before commit.

Title: `type(scope): subject`, naming a real symbol when one carries the change. Body: a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`.

Stack follow-ups by base branch. Open a PR only within the requested scope. Honor the user's requested readiness and repository rules, and default to a draft while verification is incomplete. Verification on a draft covers the checks that run on drafts. Some checks and review requests start only when a PR becomes ready, so promotion happens when landing is authorized, and the merge waits for those. Prefer an available purpose-built forge tool when it supports the operation, and never invent one. Otherwise use `gh pr create --draft --base <base-branch>` while verification is incomplete, or `origin pr create` with its draft status and base when Origin's CLI resolves the repository. A stack child's base is its parent branch. Read the returned PR's base back. Marking a PR ready is a separate action: Shipping step 4 and Autopilot-full step 5 do it right before an authorized merge, and otherwise it happens only when the user asks. Read the PR back before you report its status. When the host exposes a PR-attachment tool whose instructions require it, attach the verified URL. Otherwise return the URL and record it in the task trail. Opening a PR does not start a babysit.
