### Session pickup

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

**You own the resume point. Read the prior trail, don't redo it.**

1. Locate the prior trail through an explicitly shared chat/task reference, available scoped host history, a supplied raw transcript, decision log, or pushed branch. Desktop history tools are optional, not required in CLI. Read the overview and recent messages first, then inspect decision points. Use the history contract in CODEX.md and label summary-only evidence. Parse long supplied traces in a delegate when useful, keeping a reduced timeline in the parent. Do not scan private transcript directories or assume a prior agent is still alive.
2. Reconstruct operational state. The branch and worktree, what already landed (`git log`, `git diff` against the base), the open todos, the decisions made. The prior trail is evidence of decisions. Preserve the user's directives, distinguish inherited claims from verified state, and avoid redoing completed work without a reason.
3. Diff done vs pending. Compare what shipped against what was planned, name the resume point, do not re-run the prior repro or redo completed work. A "let me verify from scratch" pass means you're treating the trail as untrustworthy when it's authoritative.
4. Route the remaining work to the matching playbook and pick the verdict: continue the execution, ship a finished recommendation, ratify or override a prior conclusion, or postmortem a failed run. The pickup playbook ends here. The routed playbook owns the rest.
5. Verify the inherited claims against the original goal on the real artifact (the **principle-prove-it-works** skill). A passing prior self-report is not the proof.

**Reply:** where the prior agent stopped, what you inherited vs redid (ideally nothing redone), the resume point, and the outcome.
