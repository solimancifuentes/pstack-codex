### Opening a PR

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

Invoked at the end of every other playbook.

Work from a git worktree off the PR's actual base, and keep unrelated work out of it. That is trunk for independent work, and the parent branch's verified tip for a stack child. Inspect Git state first, and never use `reset --hard` or discard unrelated work to get a clean start. One writer owns each branch and worktree. Rebase into small, landable commits. Run the available `deslop` skill over the diff before commit.

Title: `type(scope): subject`, naming a real symbol when one carries the change. Body: a one-minute briefing under 40 lines with these `##` headings in order, dropping empty ones: `## Why`, `## What changed`, `## Scope`, `## Tradeoffs` (only rejected alternatives a reviewer would otherwise ask about), `## Blast Radius`, `## Verification`.

Stack follow-ups by base branch. Open a PR only within the requested scope. Prefer an available purpose-built forge tool when it supports the operation, and never invent one.

**Draft lifecycle.** A PR stays a draft until landing is authorized, unless the user or the repository's rules ask for a ready PR. Every playbook that opens, babysits, hands off, or lands a draft follows these stages.

1. **Open.** Run `gh pr create --draft --base <base-branch>`, or `origin pr create --draft --base <base-branch>` when Origin's CLI resolves the repository. A stack child's base is its parent branch, and on Origin it also passes `--stack-on <parent-pr>`. Read the base, and on Origin the parent, back.
2. **Verified draft.** The checks that run on drafts pass at this head, and the independent verdict covers it. If no check runs on drafts, and the repository's workflow triggers or rules show that every applicable check starts only when a PR becomes ready, record the checks as deferred to promotion. A failed check lookup is an error, not a deferral. A verified draft is the report a draft gets in place of merge-ready: Babysit and Autopilot owners report it, and Autopilot-stack hands it to the operator with the checks and reviews expected after promotion.
3. **Promote.** Only when landing is authorized, in Shipping step 4 or Autopilot-full step 5, or when the user asks. Run `gh pr ready <pr>` or Origin's equivalent, and read the PR back as no longer a draft.
4. **Land.** Wait for the checks and reviews that promotion starts. Merge only when the forge reports the PR mergeable: on GitHub, `mergeStateStatus` is `CLEAN` or `HAS_HOOKS`; treat `BLOCKED`, `BEHIND`, `DIRTY`, `UNKNOWN`, and any other state as unresolved. Reread the head and base SHAs; if either moved since the verdict, apply Shipping step 3's rule. Merge pinned to the head the verdict covers, with `gh pr merge <pr> --squash --match-head-commit <sha>` or `origin pr merge <pr> --match-head-commit <sha>`. Do not arm auto-merge or merge-when-ready, because neither forge documents it as bound to the verified head.

Read the PR back before you report its status. When the host exposes a PR-attachment tool whose instructions require it, attach the verified URL. Otherwise return the URL and record it in the task trail. Opening a PR does not start a babysit.
