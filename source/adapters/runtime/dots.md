# Dots adapter

Use this adapter only when the executing host is a Dot with actual native
background task or computer capabilities. A Codex task started by a Dot uses
[codex.md](codex.md). Follow [shared.md](shared.md) first.

## Coordinate through observed tools

Inspect the current Dots tool catalog and schemas. This package defines no Dots
API names and does not install a task service, computer, cloud environment, or
connector. Use only the native operations actually exposed. A missing operation
is an explicit capability gap. Keep planning, writing, and review in the shared
skills; choose the host operation only when executing their steps.

A Dot can coordinate native background agents or start and continue Codex tasks
when those operations are present, authorized, and configured. These may be
user-visible tasks, which is appropriate for intended Dots delegation. Do not
apply Codex's prohibition on making extra chats merely to replace internal
workers as a blanket ban on native Dot task coordination. Still honor the
specific tool's creation and messaging authorization rules.

For every task, record its actual identity, repository, environment, working
path, branch, acceptance checks, and completion channel. Pass the shared skill
and prompt-reference files only by a path or attachment the recipient can read.
Use a consolidated brief or a prepared package when parent and worker do not
share files. Do not assume cloud workers can read local paths on the connected
computer. A Codex worker selects its own Codex adapter and reports the actual
environment used. Preserve the original task environment when continuing it
unless a requested migration explicitly changes it.

Observe actual concurrency, budgets, and worker lifecycle limits. Poll or wait
through the supported native operation and inspect results. Keep disjoint
checkouts for writers and an independent review task when possible. Background
coordination alone provides no guarantee of VM survival, credential exclusion,
or tool isolation. Report what the configured environment actually enforces.

## Computers, history, and profiles

A Dot's cloud computer and a connected local computer are different execution
locations. Inspect which one is available and where each command runs. Access to
this plugin on a Mac does not prove that a cloud task has it. A local connected
computer must satisfy the host's actual online and app-availability requirements;
verify availability instead of promising an offline run. Browser verification
uses the actual accessible cloud or connected-computer browser with its own
permission rules.

Use native task history or supplied records within the user-authorized scope.
Do not require Codex Desktop chat APIs. Summaries remain summary evidence. Carry
only the relevant run register, source references, and selected preferences to
workers. The optional local profile belongs to the machine on which it exists.
When it is absent, use package defaults or explicit choices in the task brief,
without creating or modifying a profile during ordinary execution.

The package includes local verification and optional command helpers, so its
local-executor requirement remains meaningful. Some reasoning-only skills may
work in a Dot without a shell, but that does not establish support for installing
or executing the whole package in a shell-less host. Do not claim this adapter
is a Dots service integration or that Dots discovery has been verified merely
because the files exist.

## Ongoing responsibilities, schedules, and events

Within a requested ongoing responsibility, use supported background agents and
follow-ups to coordinate the work. Record the completion predicate, current
tasks, artifacts, and resume point. Restart or reconnect only through operations
the host supports. A long-running request does not guarantee unlimited runtime.

Create a saved schedule or event subscription only when the user requested that
facility or a controlling instruction provides that authority. First inspect
matching existing records to avoid duplicates, confirm the selected environment
and event source, preserve notification intent, then verify the actual saved
state. Supported events depend on configured connectors and current schemas.
A schedule that polls Slack or CI is not an event webhook. A one-time background
task is not a saved schedule. Installing the plugin configures none of them.

Benny-style triage is a separately scoped integration even when a supported
Slack event exists. Verify ingress, source permissions, tracker and repository
actions, review gates, and the actual credential boundary before claiming it
works. Original Cursor/Grok controls remain unsupported; do not substitute a Dot
follow-up and call it the original bot implementation.
