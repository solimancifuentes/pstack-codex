# pstack

<img src="plugins/pstack-codex/assets/pstack.png" alt="pstack glass potato logo" width="160" height="160">

An independent MIT-licensed port of [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack), maintained by Soliman Cifuentes.

The package contains 54 skills, 24 engineering principles, and 23 playbooks.
One shared workflow selects separate Codex and Dots runtime instructions from
the actual host and available tools. Codex workers started by a dot still use
the Codex adapter. This package supplies instructions, not a cloud-agent service.

## Install through Codex CLI

```sh
codex plugin marketplace add solimancifuentes/pstack-codex --ref main
codex plugin add pstack-codex@pstack-codex
```

To pin a release, use `--ref v0.2.2` instead of `--ref main`. Start a new session
after installation. Invoke `$pstack-codex:poteto-mode` and describe the task,
scope, constraints, and observable finish condition. Invoke
`$pstack-codex:setup-pstack` to inspect defaults and any local overrides.

## Install through Desktop

Add the marketplace using the command above, restart or refresh the Desktop
app, open Plugins, select the pstack marketplace, and install pstack. A custom marketplace is separate from
OpenAI's reviewed public directory. Repository publication does not imply a public-directory approval. The current submission draft reports that further
skills-only submissions are not being accepted. This release improves metadata
and privacy documentation; it does not establish directory eligibility or
clearance of the automated warnings.

For local development, register the checked-out repository instead:

```sh
codex plugin marketplace add /absolute/path/to/pstack-codex
codex plugin add pstack-codex@pstack-codex
```

## Dots

The Dots adapter uses the dot's actual background-agent, task, follow-up, and
supported event capabilities. Those depend on the account and environment.
Local skills require a connected computer online with the Desktop app open.
For cloud coding, prepare the Codex environment and make the package available
there. A cloud task does not inherit your Mac's files, dependencies, or sign-ins.

The adapter contains no fabricated Dots API names and does not provision a dot,
trigger, schedule, Slack integration, or Codex cloud environment. See
[compatibility and verification](COMPATIBILITY.md) for current evidence.

## Preferences and optional helpers

Package defaults are in `plugins/pstack-codex/defaults.json`. Optional overrides
live separately at `~/.codex/pstack-codex/preferences.json`. Missing overrides
use defaults. Package updates do not rewrite this file. Models inherit the
current session by default. Panel sizes describe total seats, not guaranteed
simultaneous workers. User and project instructions retain authority.

Skills work without Python, Bun, or the separate personal installation manager.
Optional helper preparation uses the packaged `tools/runtime.py` launcher,
Python 3.11+, and Bun on macOS/Linux. Resolve the plugin's real installed path;
do not assume the Git checkout or a fixed cache version is active. Run:

```sh
python3 /actual/plugin/path/tools/runtime.py profile show
python3 /actual/plugin/path/tools/runtime.py tools-setup --yes
python3 /actual/plugin/path/tools/runtime.py tool orch -- --help
```

Dependency installation is explicit. Mutable dependencies stay outside the
package. The launcher checks helper sources and setup receipts before running.
Ordinary installation does not relocate existing standalone skills.

## Updates, rollback, and source

Read [UPDATES.md](UPDATES.md) before changing a selected release. Maintainers
review upstream changes and publish tested port versions. End users install
those port releases, rather than pulling unadapted Cursor instructions.

Maintainer source, pinned upstream files, adapters, and tests are under `source/`.
Build with `python3 source/pstack.py build`; test with
`python3 -m unittest discover -s source/tests -v`. Export a verified build with
`python3 source/distribution.py --release /path/to/release --output /empty/output`.
The original source and license are retained. [NOTICE](NOTICE) distinguishes
original authorship from the Codex and Dots modifications.

Support: [SUPPORT.md](SUPPORT.md). Privacy: [PRIVACY.md](PRIVACY.md).
Contact: contact@solimancifuentes.com.
