You are working for the operator. The operator is the person this whole run works for, not the agent that wrote your kickoff. These rules hold for every task even where your kickoff does not repeat them. Your kickoff overrides one only when it says so in so many words. Read [CODEX.md](../../CODEX.md) for the shared runtime contract and the adapter of the host you run on.

- If you start an agent, the first line of its kickoff is `Read <path>/worker.md before anything else.`, with `<path>` the absolute path of the folder that holds this file.
- The bar in your kickoff is the whole bar. Add no check, gate, sign-off or review round above it.
- With no bar stated, the change must be no worse than its base and pass its own tests.
- Hold or block only for a failing run at this head or a bug a user would hit. Report a problem the base already has in one line.
- Never call a tool that shows a person a question. Make any choice you can undo within the scope and authority your kickoff gives, then say what you chose and why. Stop and report to your parent before a deploy, deleted data, a force-push to a shared branch, a merge, a message to someone outside the run, a credential, or a dependency setup that your kickoff does not authorize.
- Open a PR only when your kickoff asks for one, at the readiness that `playbooks/opening-a-pr.md` sets.
- PR title: `type(scope): subject`.
- PR body: 40 lines at most, with these `##` headings in this order, empty ones dropped: `Why`, `What changed`, `Scope`, `Tradeoffs`, `Blast Radius`, `Verification`.
- Put evidence logs, run histories and long tables in a file, or in a PR comment when posting is authorized, and link to them from the body.
