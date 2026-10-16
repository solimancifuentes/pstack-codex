### Worktree and simulator cleanup

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

Read CODEX.md's authority and history rules. This playbook removes user state, so its usage checks are the review.

1. Snapshot and inventory. Record `df -h /`, inspect `git worktree list --porcelain`, and measure only the returned paths. Inspect each candidate's branch, merge relation to its actual PR base, tracked changes, untracked files, ignored assets, and active processes. Do not use the retained Cursor-specific transcript helper as a usage oracle.
2. Check actual ownership. Use available host task/chat and worktree-ownership records to identify pinned, active, shared, attached, and managed worktrees. In plain CLI inspect repository records, running processes, and supplied ownership notes. Missing Desktop APIs do not prove a checkout is unused. A clean merged branch is insufficient evidence that a checkout is unused. Shared primitive and nested repro checkouts may still be in use. If ownership cannot be established, hold that candidate.
3. Verify ambiguous usage. Read only scoped chat evidence and inspect processes for candidates whose use is unclear. Queue read-only investigators within actual slots if the inventory is large. Each reports the exact path, owning chat evidence, branch, and reason to keep or remove it. A summary or age alone is not deletion authority.
4. Present lossy candidates. Tracked edits, untracked work, needed ignored assets, or in-use checkouts require an explicit decision before loss. Preserve needed files outside a checkout before removing it. State the actual files, not a generic `scratch` count. Honor existing cleanup authorization without expanding it.
5. Remove the confirmed set. For a managed attachment owned by this chat, use `archive_worktree` and its exact artifact identity so a recoverable snapshot exists. For an ordinary Git worktree within scope, prefer `git worktree remove <exact-returned-path>` without force. A refusal is a finding to inspect. Do not follow it with `rm -rf`. Re-list and measure reclaimed space.
6. Other reclaimers. Inventory simulator runtimes, derived build data, and package caches only when the user's cleanup request covers them. Determine active use and exact loss before deleting. Do not clear application history, snapshots, all simulator clones, or arbitrary caches merely because upstream listed them. Verify the resulting state with the relevant real tool.

**Reply:** disk use before and after, verified space reclaimed, removed or archived worktrees, and one reason per held candidate. Include recovery identifiers for managed archives.
