# Runtime compatibility

The shared workflow routes through `plugins/pstack-codex/CODEX.md`. The host
adapter is selected from actual executing context and tools, not from a task's
title or an instruction to pretend to be a dot.

| Capability | Codex | Dots |
| --- | --- | --- |
| Principles, planning, architecture, writing, review | Shared instructions | Shared instructions when accessible |
| Workers and independent reviewers | Actual native collaboration tools, or labeled sequential fallback | Actual background/task tools, or delegated Codex task |
| Local code, browser and app verification | Available project and host tools | Connected-computer tools when available |
| Cloud coding | Configured Codex environment | Prepared Codex cloud environment and accessible package |
| Ongoing follow-up | Session, explicitly requested goal, or supported schedule | Native follow-ups, saved schedules, supported events |
| GitHub PR attachment | Desktop attachment tool when present; CLI URL otherwise | Actual available task/forge tools |
| Private Cursor transcripts, Task APIs and Custom Modes | Unsupported | Unsupported |
| Native Claude, Fable, and Gemini panels and Cursor fast suffixes | Unsupported | Unsupported |
| Grok Bot cards and webhooks | Unsupported | Unsupported |
| Benny Slack automation | Dormant reference source | Possible future integration, not configured |

A read-only worker brief is not enforced credential isolation. Dots task context
separation does not prove exclusion of Slack credentials or write tools. Native
task APIs and supported event sources must be observed before use. Connecting a
plugin does not establish a schedule or authorize messages to other people.

Optional helper commands require Python 3.11+ and POSIX support on
macOS/Linux, and the watcher also needs Bun. Their absence does not prevent the Markdown workflows, but in the unpublished 0.2.0 checkout, on GitHub, Babysit's merge-ready verdict and the landings in Shipping and Autopilot need the prepared watcher; without it they report the forge's state and leave the merge to the user. The
`statechart` skill needs Node 22.18+ (23.6+ on Node 23), Bun 1.1.5+, or Deno 2+,
and Java with TLC.
Installing Java and TLC through `mise`, or the Pele renderer through npm, is
dependency setup that requires explicit authorization. The existing
advanced personal manager additionally has a fixed default Codex-home boundary.

## Prepared upstream update

The development checkout prepares port 0.2.0 from upstream pstack 0.15.46. It
contains 58 skills and 22 playbooks. The [update record](verification/upstream-0.15.46.md)
records the local checks and their limits. Native installation and discovery for
this source have not been rerun; the [0.15.27 cloud validation](verification/cloud-validation-upstream-0.15.27.md)
covers the earlier source only. The v0.1.0 evidence below remains the historical
release baseline. No new release is published.

## Verification boundary

v0.1.0 is the first supported release and the public starting point. It includes
the shared skills, host adapters, glass-potato logo, and explicit privacy policy.
Public directory eligibility requires the actual portal checks; local
verification does not establish approval.

For this baseline, 70 automated tests passed. Fresh native app-server discovery
found all 54 skills with zero parse errors. Earlier development checks also
exercised the Codex workflow, host-adapter selection, native installation, and
update and rollback behavior. Those lifecycle receipts are internal development
evidence, not a list of earlier supported releases or available downgrade tags.
See `verification/` for the recorded checks.

Live Dots execution has not been verified. Desktop visual interaction was blocked
by the computer-use tool; its native plugin loader was verified separately.
The Dots adapter is experimental until a live Dots run exercises its actual tools.

The release verification record distinguishes local unit/subprocess tests,
native CLI/app-server discovery, Desktop UI inspection, behavioral model checks,
and live Dots operation. A simulated Dots brief is a contract test only.
No live Dots result is inferred from the product documentation or Codex tests.
Public-directory scans, approval, and publication are separate from local checks.

Current Dots behavior is documented at
https://learn.chatgpt.com/docs/dots and
https://learn.chatgpt.com/docs/dots/tasks-and-memory.
