# pstack runtime entrypoint

This compatibility filename routes the shared pstack plugin on Codex and Dots.
Read [the shared contract](runtime/shared.md), then the adapter for the actual
executing host.

- A Codex CLI, Desktop, or cloud worker uses [Codex](runtime/codex.md).
- A Dot coordinating work with its native background task or computer tools uses
  [Dots](runtime/dots.md).

Select from the current host instructions and available tool schemas. A Codex
task started by a Dot still uses the Codex adapter. A mention of Dots in the
request does not change the executing host. If the host cannot be established,
use only observed capabilities and state the missing evidence. Do not infer a
remote environment, schedule, or API from these files.

The same skills and playbooks run through either adapter. The original pinned
Cursor source records provenance. Its tools and installation instructions are
not provided by this package.
