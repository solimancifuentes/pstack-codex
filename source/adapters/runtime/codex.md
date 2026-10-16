# Codex adapter

Use this adapter when execution is in a Codex CLI, Desktop, or cloud task,
including a Codex task launched by a Dot. Follow [shared.md](shared.md) first.

## Tools and delegation

Use current native collaboration tools when exposed. These may include
`collaboration.spawn_agent`, `send_message`, `followup_task`, `interrupt_agent`,
`list_agents`, and `wait_agent`; inspect the actual schemas before use. The
current API may not provide Cursor's `Task` subtype selector, a read-only switch,
cloud selector, fast suffix, or background flag. Do not supply absent fields.
Queue panel seats within the reported limit, including nested workers and the
coordinator. Native child workers ordinarily share the current host and tool
access; rely on explicit environment guarantees when they differ.

The agent prompt references do not register native agent types. Give every
worker the actual checkout and readable plugin paths. A cloud Codex task uses
its configured cloud environment. It does not automatically inherit files,
profiles, tools, credentials, or uncommitted state from a Mac or the Dot that
started it. Inspect the task's environment and repository state before work.

Do not create user-owned chats merely to emulate an unavailable internal
collaboration tool. Creating or messaging a separate chat follows the user's
actual authorization and the client tool's instructions. This Codex-specific
rule does not prevent a Dot from using its intended native task delegation.

## CLI and Desktop capabilities

The core skills work in CLI without Desktop tool access. Use the current
conversation, user-supplied history, Git, PRs, and durable task records. If scoped
`list_threads` or `read_thread` tools are available, they can supplement history;
otherwise state any coverage gap. Do not require them or inspect private caches
as a substitute.

Use an available managed-worktree tool or ordinary safe `git worktree` commands,
according to the current environment and repository rules. For cleanup, inspect
ownership and live processes. If Desktop attachment or chat-ownership tools are
absent and ownership cannot be proved another way, retain that candidate.

After creating a PR, call `attach_artifact` with its verified URL when that tool
is exposed and its instructions require it. Otherwise return the verified PR
link in the CLI response and task record. Missing attachment UI does not block
creation or verification of an authorized PR. Use actual browser/app tools when
present and a project CLI harness when appropriate. Never claim a Desktop UI or
computer tool exists in plain CLI.

## Long work

An active task runs within its actual turn, environment, and budget. A local
child or shell watcher does not guarantee durable execution or waking a finished
chat. Create a goal only when explicitly requested or required by a controlling
instruction; inspect and use its real status and budget tools when present.

For requested recurring follow-up, use the available native automation or
heartbeat tool under its actual instructions. Inspect existing matching jobs,
verify the returned schedule and target, and stay quiet on unchanged state
unless the user requested periodic reports. If that facility is absent, provide
a resumable checkpoint and state the limitation. Never invent `/loop`, an event
webhook, or a scheduler because the playbook would benefit from one.

A Dot may own the ongoing responsibility outside this task. In that case return
receipts and a clean resume point to its actual task result channel. The Codex
worker does not become a Dot or acquire its background capabilities.
