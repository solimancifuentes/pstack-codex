# pstack for Codex

<img src="plugins/pstack-codex/assets/pstack.png" alt="pstack glass potato logo" width="160" height="160">

[pstack](https://github.com/cursor/plugins/tree/f713f14203cd6420cec13cd7c55c32d598dbab68/pstack) is [Lauren Tan's](https://x.com/poteto) engineering workflow. Lauren, [@poteto on X](https://x.com/poteto), created the original skills, principles, playbooks, and agent prompts. All credit for the original pstack belongs to her.

This repository is an independent adaptation for Codex, maintained by Soliman Cifuentes. It keeps Lauren's approach and changes the parts that depend on Cursor's tools, model routing, and installation format.

An agent can write a plausible fix before it understands the bug. Then you spend your time finding out whether the fix actually works. pstack puts that work into the task itself. Reproduce the problem. Understand the data and callers. Make the change. Verify the behavior against something you can inspect.

That also gives parallel work a useful constraint. Each worker gets a scope and a check, and the coordinator has to assemble evidence before declaring the job done. More workers only help if you can tell what they did.

The port contains **54 skills, 24 engineering principles, and 23 playbooks**. Codex supplies the models, execution tools, and permissions. pstack supplies the workflow.

## install

You can install from GitHub now. This repository is a custom Codex marketplace; pstack is not currently listed in OpenAI's public Plugins directory.

`v0.2.2` is the starting release. If you're already using it, no update or rollback is needed.

With a recent [Codex CLI](https://learn.chatgpt.com/docs/codex/cli):

```sh
codex plugin marketplace add solimancifuentes/pstack-codex --ref v0.2.2
codex plugin add pstack-codex@pstack-codex
codex plugin list --marketplace pstack-codex --json
```

The tag pins the reviewed port release. Check that the result shows version `0.2.2`, then start a new chat. If your CLI does not recognize `codex plugin`, update it before continuing.

In Codex Desktop, restart the app after the CLI installation. You can also run only the first command to register the catalog, restart the app, then open Plugins, select the pstack custom marketplace, and install pstack there. Adding our catalog does not require a public-directory listing.

For local development, replace the first command with:

```sh
codex plugin marketplace add /absolute/path/to/pstack-codex
```

## get started

Start with [`poteto-mode`](plugins/pstack-codex/skills/poteto-mode/SKILL.md). Give it the task, the boundaries, and what you expect to observe when it works:

```text
$pstack-codex:poteto-mode The list scrolls every 750 ms while idle. Reproduce it,
find the cause, and fix it. Verify that it stays still and that keyboard
navigation still works. Keep the change in this branch for review.
```

Use [`setup-pstack`](plugins/pstack-codex/skills/setup-pstack/SKILL.md) if you want to inspect or change model and panel choices:

```text
$pstack-codex:setup-pstack Show my current choices before changing anything.
```

Setup is optional. Models inherit the current session by default, and an absent profile uses the package defaults.

If you're unsure which workflow fits, ask [`poteto-help`](plugins/pstack-codex/skills/poteto-help/SKILL.md). It can explain the choice and give you a prompt to use.

## usage

[`poteto-mode`](plugins/pstack-codex/skills/poteto-mode/SKILL.md) reads the complete workflow, chooses a playbook, and calls the other skills as the work needs them. You can also call a skill directly. In Codex, use the qualified `$pstack-codex:skill-name` form shown here, or select the skill from the available skill picker.

```text
$pstack-codex:poteto-mode Walk through how cancellation works. Investigate only;
do not change code. Show the path from the button to the worker stopping.
```

```text
$pstack-codex:poteto-mode Migrate callers to the asynchronous store in small,
verifiable steps. Preserve behavior. Open a draft PR when the checks pass.
```

The playbook follows your requested endpoint. Asking for an investigation does not authorize edits, and a workflow name does not authorize merges, deployment, messages, or changes to your settings. Long runs also depend on the session and tools actually available. Cursor's persistent Custom Modes and `/loop` command do not carry over to Codex.

<details>
<summary>the twenty-three playbooks</summary>

| playbook | for |
| --- | --- |
| [investigation](plugins/pstack-codex/skills/poteto-mode/playbooks/investigation.md) | Answer a question without changing code. |
| [bug fix](plugins/pstack-codex/skills/poteto-mode/playbooks/bug-fix.md) | Reproduce a defect, trace its cause, and verify the fix. |
| [perf](plugins/pstack-codex/skills/poteto-mode/playbooks/perf-issue.md) | Improve measured performance against a baseline. |
| [hillclimb](plugins/pstack-codex/skills/poteto-mode/playbooks/hillclimb.md) | Improve one metric through measured experiments. |
| [runtime forensics](plugins/pstack-codex/skills/poteto-mode/playbooks/runtime-forensics.md) | Investigate a live leak, spin, or glitch. |
| [trace forensics](plugins/pstack-codex/skills/poteto-mode/playbooks/trace-forensics.md) | Explain a captured profile, trace, or heap snapshot. |
| [feature](plugins/pstack-codex/skills/poteto-mode/playbooks/feature.md) | Build new behavior around an explicit data shape. |
| [refactoring](plugins/pstack-codex/skills/poteto-mode/playbooks/refactoring.md) | Change structure while preserving behavior. |
| [prototype](plugins/pstack-codex/skills/poteto-mode/playbooks/prototype.md) | Compare an idea cheaply before committing to it. |
| [visual parity](plugins/pstack-codex/skills/poteto-mode/playbooks/visual-parity.md) | Compare two interfaces against the same visual target. |
| [authoring a skill](plugins/pstack-codex/skills/poteto-mode/playbooks/authoring-a-skill.md) | Write or revise a skill. |
| [eval](plugins/pstack-codex/skills/poteto-mode/playbooks/eval.md) | Compare prompt or skill changes through blinded evaluation. |
| [babysit](plugins/pstack-codex/skills/poteto-mode/playbooks/babysit.md) | Resolve PR conflicts, review threads, and CI problems. |
| [shipping](plugins/pstack-codex/skills/poteto-mode/playbooks/shipping.md) | Verify a stack before an authorized landing. |
| [autonomous run](plugins/pstack-codex/skills/poteto-mode/playbooks/autonomous-run.md) | Carry a scoped long task through to its endpoint. |
| [orchestrate](plugins/pstack-codex/skills/poteto-mode/playbooks/orchestrate.md) | Coordinate a project across phases and workers. |
| [autopilot-full](plugins/pstack-codex/skills/poteto-mode/playbooks/autopilot-full.md) | Coordinate independent PRs through review and authorized merging. |
| [autopilot-stack](plugins/pstack-codex/skills/poteto-mode/playbooks/autopilot-stack.md) | Build a linear stack for the operator to review and land. |
| [session pickup](plugins/pstack-codex/skills/poteto-mode/playbooks/session-pickup.md) | Resume another session's work from its actual state. |
| [pause safely](plugins/pstack-codex/skills/poteto-mode/playbooks/pause-safely.md) | Leave a checkpoint that another session can resume. |
| [multi-phase plan](plugins/pstack-codex/skills/poteto-mode/playbooks/multi-phase-plan.md) | Break larger work into verifiable phases. |
| [worktree cleanup](plugins/pstack-codex/skills/poteto-mode/playbooks/worktree-cleanup.md) | Review and safely remove eligible worktrees and other supported artifacts. |
| [opening a PR](plugins/pstack-codex/skills/poteto-mode/playbooks/opening-a-pr.md) | Prepare ordered commits and a useful PR description. |

</details>

## skills

Most of the time, start with `poteto-mode` and let it route. Use a specific skill when you already know which part of the work needs attention:

```text
$pstack-codex:how How does a cancelled run stop its child workers?
```

```text
$pstack-codex:interrogate Review this diff. Look for behavior that the existing
tests miss, and keep the review read-only.
```

<details>
<summary>the workflow skills</summary>

| skill | use it when |
| --- | --- |
| [poteto-mode](plugins/pstack-codex/skills/poteto-mode/SKILL.md) | You want the complete engineering workflow. |
| [poteto-help](plugins/pstack-codex/skills/poteto-help/SKILL.md) | You need help choosing a skill or framing a task. |
| [in-your-own-words](plugins/pstack-codex/skills/in-your-own-words/SKILL.md) | You want the agent to explain its understanding first. |
| [sharpen](plugins/pstack-codex/skills/sharpen/SKILL.md) | The request needs a clearer problem or success condition. |
| [how](plugins/pstack-codex/skills/how/SKILL.md) | You need to understand how a subsystem works. |
| [why](plugins/pstack-codex/skills/why/SKILL.md) | You need the evidence behind a design or decision. |
| [recall](plugins/pstack-codex/skills/recall/SKILL.md) | You need to rebuild context from scoped, accessible history. |
| [ketchup](plugins/pstack-codex/skills/ketchup/SKILL.md) | You need a brief account of what changed while you were away. |
| [blast-radius](plugins/pstack-codex/skills/blast-radius/SKILL.md) | A small change may affect more than its immediate caller. |
| [architect](plugins/pstack-codex/skills/architect/SKILL.md) | Types, callers, and module boundaries need design work. |
| [arena](plugins/pstack-codex/skills/arena/SKILL.md) | You want competing attempts at the same problem. |
| [swarm](plugins/pstack-codex/skills/swarm/SKILL.md) | Different parts of the work can proceed independently. |
| [interrogate](plugins/pstack-codex/skills/interrogate/SKILL.md) | You want independent reviewers to challenge a diff. |
| [automate-me](plugins/pstack-codex/skills/automate-me/SKILL.md) | You want a personal mode based on your working conventions. |
| [make-bot-ui](plugins/pstack-codex/skills/make-bot-ui/SKILL.md) | You need an explanation of the unavailable original bot integration. Diagnostic only. |
| [setup-pstack](plugins/pstack-codex/skills/setup-pstack/SKILL.md) | You want to inspect or change supported workflow preferences. |
| [reflect](plugins/pstack-codex/skills/reflect/SKILL.md) | You want to turn a session's mistakes into useful changes. |
| [correct](plugins/pstack-codex/skills/correct/SKILL.md) | A correction should change how the agent works next time. |
| [figure-it-out](plugins/pstack-codex/skills/figure-it-out/SKILL.md) | A scoped task needs sustained investigation and execution. |
| [bro](plugins/pstack-codex/skills/bro/SKILL.md) | You want the last reply restated in plain human language. |
| [teach](plugins/pstack-codex/skills/teach/SKILL.md) | You want an explanation that builds understanding. |
| [tdd](plugins/pstack-codex/skills/tdd/SKILL.md) | You want behavior established by a failing test before implementation. |
| [unslop](plugins/pstack-codex/skills/unslop/SKILL.md) | Prose needs a pass for filler and artificial phrasing. |
| [no-comments](plugins/pstack-codex/skills/no-comments/SKILL.md) | Comments need an independent review against what the code can express. |
| [technical-writing](plugins/pstack-codex/skills/technical-writing/SKILL.md) | Engineering prose needs clear terms and visible reasoning. |
| [typescript-best-practices](plugins/pstack-codex/skills/typescript-best-practices/SKILL.md) | TypeScript types and boundaries need review. |
| [benchmark-checklist](plugins/pstack-codex/skills/benchmark-checklist/SKILL.md) | A performance claim needs a trustworthy measurement. |
| [create-verification-skill](plugins/pstack-codex/skills/create-verification-skill/SKILL.md) | A project needs a repeatable way to verify real behavior. |
| [maintain-verification-skill](plugins/pstack-codex/skills/maintain-verification-skill/SKILL.md) | A verification workflow needs to keep up with the product. |
| [show-me-your-work](plugins/pstack-codex/skills/show-me-your-work/SKILL.md) | You want a decision trail you can inspect later. |

</details>

## the `poteto-agent` and Comment Sicko subagents

The chat receiving `poteto-mode` owns the playbook and coordinates the work. The [`poteto-agent`](plugins/pstack-codex/agents/poteto-agent.md) reference gives a delegate the same workflow and principles, plus its own scope and checks.

[Comment Sicko](plugins/pstack-codex/agents/comment-sicko.md) reviews comments read-only, usually through [`no-comments`](plugins/pstack-codex/skills/no-comments/SKILL.md). It questions narration and workarounds while retaining supported license headers, public API contracts, and externally imposed constraints.

These are prompt references for Codex's available workers. They do not register Cursor's named `subagent_type` values. If parallel workers or independent models aren't available, the port must say so rather than claim it ran a panel.

## principles

The twenty-four principle skills give the workflow its engineering rules. `poteto-mode` reads their index and opens the relevant full rule when applying one. They cover the design of the change as well as the evidence needed to trust it.

<details>
<summary>all twenty-four principles</summary>

| principle | rule |
| --- | --- |
| [laziness-protocol](plugins/pstack-codex/skills/principle-laziness-protocol/SKILL.md) | Prefer the smallest change that solves the problem. |
| [foundational-thinking](plugins/pstack-codex/skills/principle-foundational-thinking/SKILL.md) | Settle the core data structures before writing downstream logic. |
| [redesign-from-first-principles](plugins/pstack-codex/skills/principle-redesign-from-first-principles/SKILL.md) | Design as though the requirement had been there from the start. |
| [attack-the-premise](plugins/pstack-codex/skills/principle-attack-the-premise/SKILL.md) | Test the shared assumption when repeated fixes fail. |
| [subtract-before-you-add](plugins/pstack-codex/skills/principle-subtract-before-you-add/SKILL.md) | Remove obsolete code before building around it. |
| [minimize-reader-load](plugins/pstack-codex/skills/principle-minimize-reader-load/SKILL.md) | Reduce indirection and the state a reader must remember. |
| [outcome-oriented-execution](plugins/pstack-codex/skills/principle-outcome-oriented-execution/SKILL.md) | Organize a migration around its target architecture. |
| [experience-first](plugins/pstack-codex/skills/principle-experience-first/SKILL.md) | Make the result work well for the person using it. |
| [exhaust-the-design-space](plugins/pstack-codex/skills/principle-exhaust-the-design-space/SKILL.md) | Compare competing designs before committing. |
| [build-the-lever](plugins/pstack-codex/skills/principle-build-the-lever/SKILL.md) | Build a repeatable tool for the work or its verification. |
| [model-the-domain](plugins/pstack-codex/skills/principle-model-the-domain/SKILL.md) | Express the domain in its data structures. |
| [boundary-discipline](plugins/pstack-codex/skills/principle-boundary-discipline/SKILL.md) | Validate at boundaries and keep internal logic simple. |
| [type-system-discipline](plugins/pstack-codex/skills/principle-type-system-discipline/SKILL.md) | Encode valid states and contracts in types. |
| [make-operations-idempotent](plugins/pstack-codex/skills/principle-make-operations-idempotent/SKILL.md) | Make retries converge on the same result. |
| [migrate-callers-then-delete-legacy-apis](plugins/pstack-codex/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | Move callers and remove the obsolete API together. |
| [separate-before-serializing-shared-state](plugins/pstack-codex/skills/principle-separate-before-serializing-shared-state/SKILL.md) | Remove unnecessary shared state before adding coordination. |
| [prove-it-works](plugins/pstack-codex/skills/principle-prove-it-works/SKILL.md) | Verify the actual artifact before declaring completion. |
| [fix-root-causes](plugins/pstack-codex/skills/principle-fix-root-causes/SKILL.md) | Trace the symptom to the first broken assumption. |
| [sequence-verifiable-units](plugins/pstack-codex/skills/principle-sequence-verifiable-units/SKILL.md) | Make each phase end in a state you can check. |
| [test-behavior-not-implementation](plugins/pstack-codex/skills/principle-test-behavior-not-implementation/SKILL.md) | Test what callers can observe. |
| [explain-the-number](plugins/pstack-codex/skills/principle-explain-the-number/SKILL.md) | Explain what a measurement actually measures. |
| [guard-the-context-window](plugins/pstack-codex/skills/principle-guard-the-context-window/SKILL.md) | Delegate bulk investigation and return concise findings. |
| [never-block-on-the-human](plugins/pstack-codex/skills/principle-never-block-on-the-human/SKILL.md) | Continue authorized work while preserving required approvals. |
| [encode-lessons-in-structure](plugins/pstack-codex/skills/principle-encode-lessons-in-structure/SKILL.md) | Turn a lesson into a check or structural constraint. |

</details>

## make it yours

You may want the engineering rules and a different working style. [`automate-me`](plugins/pstack-codex/skills/automate-me/SKILL.md) drafts a personal mode from the conversation and other history you explicitly put in scope. It doesn't require access to Cursor transcripts.

[`setup-pstack`](plugins/pstack-codex/skills/setup-pstack/SKILL.md) handles supported model and panel preferences. Optional overrides live at `~/.codex/pstack-codex/preferences.json`, outside the installed package, so release updates and rollback preserve them. A cloud worker needs its own accessible preferences or a brief containing the relevant choices.

The default panels have two seats. Seats describe how much independent work to request; the available worker slots determine what can run simultaneously. Exact model and reasoning choices still depend on your host and account.

## optional helpers and automations

The Markdown workflows work without Python or Bun. If you want the bundled orchestration and PR-watching helpers, their launcher needs Python 3.11+, Bun, and macOS/Linux support. Resolve the plugin's actual installed location, then run:

```sh
python3 /actual/plugin/path/tools/runtime.py profile show
python3 /actual/plugin/path/tools/runtime.py tools-setup --yes
python3 /actual/plugin/path/tools/runtime.py tool orch -- --help
```

Dependency setup is explicit, and mutable helper data stays outside the package. Read [COMPATIBILITY.md](COMPATIBILITY.md) before relying on a workflow tied to a particular host.

Cursor's Grok Bot and Benny Slack integrations are not operational in this port. Installing pstack does not create a bot, schedule, trigger, or background service. You can use available native scheduling tools for separately requested work.

### experimental Dots support

The same package includes a Dots adapter. Local workflows need a connected computer; cloud Codex tasks need the package and dependencies in their own environment. A Codex worker started by a Dot uses the Codex adapter. Live Dots execution remains unverified. See the [compatibility record](COMPATIBILITY.md) for the tested boundaries. No hosted MCP service is included.

## updates and source

The port is based on Lauren's pstack at [`850d7f2e9f5e55dff7eb00a0a479337fe79eb22f`](https://github.com/cursor/plugins/tree/850d7f2e9f5e55dff7eb00a0a479337fe79eb22f/pstack). [`source/source.lock.json`](source/source.lock.json) records the exact upstream files included in the adaptation.

`v0.2.2` is the first supported release, with no earlier public version to update from or roll back to. [UPDATES.md](UPDATES.md) explains how future releases will handle updates and rollback. Maintainer updates review upstream changes and publish tested port versions. Install those releases rather than copying unadapted Cursor instructions into Codex.

The reproducible maintainer source, upstream snapshot, adapters, and tests are in [`source/`](source/). Build with `python3 source/pstack.py build` and run checks with `python3 -m unittest discover -s source/tests -v`.

## license

MIT. Lauren Tan retains the original pstack authorship and copyright. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Soliman Cifuentes maintains the Codex adaptation and its runtime changes.

Support: [SUPPORT.md](SUPPORT.md). Privacy: [PRIVACY.md](PRIVACY.md). Contact: contact@solimancifuentes.com.
