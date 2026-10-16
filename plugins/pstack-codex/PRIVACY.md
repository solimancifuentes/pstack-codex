# Privacy policy

Effective October 15, 2026.

Soliman Cifuentes publishes pstack, an independent open-source collection of
engineering workflows and optional local helper scripts. Contact
contact@solimancifuentes.com for privacy questions or deletion requests.

## Data used during a workflow

The package includes no publisher-operated server, analytics collector, or
telemetry endpoint. It does not send your profile, code, or task records to
Soliman Cifuentes through a service supplied by this package.

When you invoke a workflow, your chosen host and connected tools may process
prompts, source code, task files, selected conversation context, repository
metadata, and generated outputs. These inputs can contain names, usernames,
email addresses, file paths, or other personal information included in your
task. The purpose is to perform the work you authorize, such as planning,
implementation, review, and verification.

Your host, including OpenAI products when used, and the connected services you
use process their copies under their own terms, permissions, retention policies,
and account controls. The publisher does not receive those copies merely
because you install or invoke pstack.

## Local preferences and task records

Optional preferences include model and workflow choices, role settings, and
panel sizes. The default profile is
`~/.codex/pstack-codex/preferences.json`, or a profile path you select.

Optional helper preparation stores dependency packages, prepared script copies,
hashes, setup receipts, and caches under `~/.local/state/pstack-codex` by default.
You can select a different location with `PSTACK_STATE_HOME` or `--state-root`.
The separate personal installation manager also keeps releases, installation
history, migration backups, and helper files under `~/.codex/pstack-codex`.

Optional bookkeeping can store task identifiers, branches, pull-request
identifiers, commit hashes, briefs, decisions, evidence references, reviewer
names, timestamps, and status. The caller selects the task-store directory or
log path. These records support coordination, verification, and resuming work.

These local records have no automatic time-based expiry. They remain until you
or your environment remove or replace them. Some helper commands replace
status files or delete consumed inbox pointers. Plugin updates and uninstall
do not purge separately stored preferences, task records, backups, or caches.

You control these local files. After stopping active helpers, you can delete the
optional profile, selected helper-state directory, and task stores or logs you
created. Review migration backups before removing the personal manager
directory. Local deletion does not remove copies in host history, cloud
workspaces, repository commits, backups, or connected services. Use those
services' controls for their copies.

## Services contacted by optional tools

Invoked repository helpers use your existing command-line tools to query forge
services such as GitHub for repository and pull-request information. Explicit
dependency preparation contacts the package registry configured for Bun.
Maintainer upstream checks contact GitHub's API and source-download service.
Other workflow actions use the connected services authorized for the task.

These services receive the requests needed for those operations and process
them under their own policies. Helpers use authentication already available to
your host tools. The package does not create a separate credential vault or
credential-isolation boundary. Do not put passwords, tokens, or other secrets
in a profile, task log, support email, or public issue.

## Support email

If you email contact@solimancifuentes.com, the publisher receives your sender
name and email address, message contents, attachments, and any diagnostic
information you choose to include. This information is used to respond to your
request and investigate reported problems.

Soliman Cifuentes is the only person with access to the support inbox. Email
service providers also process messages to deliver and store email. Support
correspondence is not automatically published as a GitHub issue.

Support emails and attachments are deleted from the publisher's mailbox within
90 days after the last exchange about the request. You can request earlier
deletion by emailing contact@solimancifuentes.com from the address used for
support. The publisher deletes the correspondence and attachments under his
control within seven calendar days, including copies in sent mail and trash,
and keeps no separate archive afterward.

This deletion commitment covers the publisher's copies. Email service
providers' independently retained technical records or backups are governed by
their own policies. The publisher cannot promise deletion from systems outside
his control.

## Public GitHub issues

If you open or comment on a public issue, GitHub processes and displays your
account identity, issue text, comments, and attachments. The purpose is public
project support and issue tracking. This information is visible to other people
and remains until edited or removed through GitHub's controls.

Use your GitHub account controls to manage content you posted. You can also
email contact@solimancifuentes.com to request removal of personal information
from project content the publisher controls. The publisher removes that
information within seven calendar days and keeps no separate private archive.
Copies made by other people, search engines, forks, or GitHub's own systems
remain subject to those parties' controls and policies. Avoid posting secrets
or private diagnostic data in public issues.
