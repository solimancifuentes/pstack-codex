### Autopilot-stack

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

Run the Autopilot-full playbook, but do not merge.

1. **In place of step 5, stop at verified.** Stop when each PR is a verified draft at its current head under stage 2 of the draft lifecycle in `playbooks/opening-a-pr.md`, then hand the PRs to the operator with the checks and reviews expected after promotion. After the handoff, nobody pushes without the operator's go. Every audit checkpoint prompt names this file, so each checkpoint sees the no-merge rule.
2. **Stack a PR only when it builds on another PR.** This is the one exception to step 3. Base the PR on the other PR's branch in place of trunk, per `playbooks/opening-a-pr.md`. In place of step 2's rebase onto trunk, each PR rebases onto its parent PR's branch, and the stack root rebases onto trunk. A new head on the lower PR restacks the PRs above it. A PR keeps its verdict only under Shipping step 3's rule: its own diff is byte-identical, whitespace included, and the parent's change cannot affect it under Autopilot-full step 5's test. Otherwise rerun the affected verification at the restacked head.

**Reply:** list each PR with its verdict, in place of what merged.
