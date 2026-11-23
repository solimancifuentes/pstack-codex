# Upstream pstack 0.15.46 update

This checkout prepares unpublished port 0.2.0 from upstream pstack 0.15.46.
Published installations remain on v0.1.0 until a reviewed port release is
available.

## Source identity

The previous pin is pstack 0.15.27 at
`0148b78c56c72a1b8412055913c79f767095b217`. The update pins
[pstack 0.15.46 at 7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9](https://github.com/cursor/plugins/commit/7a583913eb1b8d1a0ee76753d1a2cf072e7b54f9).
Both upstream plugin manifests report 0.15.46. The upstream repository has no
version tags, so this identity comes from its versioned source.

The source manager fetched the snapshot from GitHub's archive endpoint. A
`git archive` of the same commit from a fresh clone of
`https://github.com/cursor/plugins.git` matches all 553 imported files byte for
byte, including executable bits. The [delta](upstream-0.15.46-delta.json) adds
413 files, changes the content of 82, and removes 31. Git also shows two
mode-only changes, which make `watch-pr` and `log.sh` executable. The source
lock hashes content only, so the build does not recheck file modes. 410 of the added files belong to the new
`statechart` skill and its test corpus.

## Upstream changes

Upstream made 33 pstack commits in this range. The ones that affect the port:

- New skills: `maintain-formal-verification-skill`, `statechart`, and
  `ketchup-video`. The port now has 58 skills.
- Most skill texts are shorter. `how`, `why`, `reflect`, and `architect` lost
  their reference prompts and multi-phase flows. `interrogate` now keeps only
  findings that an adversary proves with a run.
- The Orchestrate playbook and the `orch` scripts were deleted. The port now
  has 22 playbooks.
- `poteto-mode` gained `worker.md`, a set of rules that every started agent
  reads first.
- Model routing moved from Opus and Grok to Opus, Fable, and Gemini, capped at
  xhigh. Upstream retired the `architect` panel and several roles.

## Adaptations

- 49 overlay files follow the new upstream text. Eight overlays were retired:
  `architect` and `why` are now host-neutral upstream, and the `how` and
  `reflect` reference prompts and the Orchestrate playbook no longer exist.
- New overlays: `poteto-mode/worker.md` keeps the shared authority boundary and
  the port's draft-until-verified PR policy. `statechart/SKILL.md` resolves the
  installed skill path and treats the `mise` Java and TLC install and the Pele
  install as explicit dependency setup. Without install authority, it
  requires absolute `TLA2TOOLS` and `JAVA` paths before each run, because the
  command installs Java and TLC whenever its own `mise` lookup fails. It
  treats a `--view` module as code. `ketchup-video` returns the
  video path when the host cannot embed it.
- Every worker kickoff, from any skill, starts with the `worker.md` line. The
  shared contract carries that rule, so standalone `how`, `arena`, and
  `interrogate` runs get it too.
- Inherited roles omit model and effort overrides. Arena substitutes a model
  only when the user's selection allows it. Otherwise it drops the seat, and
  it reports when fewer than two runners remain.
- Opening a PR uses `gh pr create --draft` until verification is done, and
  Babysit passes `--allow-draft` for such a PR and never marks it ready.
- `reflect` edits pstack through its source overlays, never by copying an
  installed, already-normalized skill into the source tree.
- The `orch` helper is removed from `tools/runtime.py`, the manager, the shared
  contract, and the tests. `watch-pr` and `log` remain.
- The default arena and interrogate panels have three seats, matching
  upstream's panel size. The `architect` panel default is gone. Existing
  profile keys are preserved, and `setup-pstack` reports retired roles. A
  profile that equals the v0.1.0 snapshot the manager copied is treated as old
  defaults, and `setup-pstack` offers to remove it. `profile set` now removes
  a key set to `null`, and rejects an arena panel below two seats.
- The build lint now also rejects `claude-fable-5-2-` and `gemini-4-neon-`
  slugs in packaged skills, as it already did for Opus and Grok slugs.
- Codex and Dots adapters, external preferences, explicit invocation policy,
  and MIT attribution are unchanged.

## Verification

- `python3 source/tests/verify_repository.py` rebuilds release
  `7a583913eb1b-28e89fc9ae92` and matches the tracked plugin, `release.json`, the mirrored
  documents, and the repository `NOTICE` and `LICENSE`.
- [All 92 Python tests pass](unit-tests-upstream-0.15.46.txt), including new
  tests for `null` removal, including under an absent parent, the arena minimum, and the Fable, Gemini, and Opus
  slug lint. They cover
  reproducible builds and ZIP export, contained Markdown links, metadata and
  invocation policy, profile preservation, update and rollback recovery, and
  helper runtime boundaries.
- The `statechart` launcher, run with `sh` from the built package on Node 26,
  parses its arguments. Without TLC or `mise` it stops with the documented
  message and writes no output folder.

## Not verified

- Native Codex installation, update, rollback, and loader discovery were not
  rerun for this source. The [0.15.27 cloud validation](cloud-validation-upstream-0.15.27.md)
  covers only the earlier source. Repeat it before publication.
- The upstream `watch-pr` Bun tests and strict typecheck did not run, because
  Bun is not installed on the maintainer machine.
- `statechart` was not run against a real TLC, and the Pele renderer was not
  exercised. The Astra review ran statechart's own test files with fake Java:
  225 passed and 62 skipped. Of four first-run failures, three passed when
  rerun with the process inspection they need, and the fourth is the macOS
  symlink fixture listed below.

## Review

Two independent read-only reviews ran on head `b1c85a2`. One was a fresh
Claude Opus 5.5 worker. The other was GPT-6.2 Astra at xhigh reasoning through
Codex. Neither found a blocking defect. Their findings on the port's own
adaptations and documents are fixed above. An Astra re-check of the fix commit
found five remaining gaps: null deletion under an absent parent, a premature
"verified" claim in Babysit, arena's inherited fallback, the statechart install
guidance, and a stale repository `NOTICE`. Those are fixed too.

A follow-up review loop then ran Claude Opus 5.5, GPT-6.2 Astra at xhigh, and
GPT-6.2 Sol at max reasoning on the merged result, fixing each round's findings
until a round came back clean. Round 1 led to these changes:

- Shipping and Autopilot-full now mark a policy draft ready right before an
  authorized merge, read it back, and recheck merge gates that promotion can
  open. Shipping's queued watcher passes `--allow-draft`. Babysit reads an
  `--allow-draft` `READY` as ready to promote, not ready to merge, and its
  Origin `check` mode no longer starts a watch.
- The personal manager no longer copies the packaged defaults into a new
  user's profile, which would have masked every later default change.
- With an older active release, such as v0.1.0 after a rollback, the manager
  still runs that release's `orch` helper.
- A deletion-only profile change no longer replaces an existing scalar. A saved
  one-seat arena no longer blocks `profile show` or unrelated edits; it shows a
  warning instead.
- Arena stops before judging when fewer than two artifacts remain. Interrogate
  states that a single adversary can run.
- Eval keeps workflow paths out of candidate briefs so blinding holds, and
  lowers reasoning only when the user's selection permits it.
- Feature and Refactoring read the same `feature, refactoring` role key as the
  coordinator.
- Opening a PR bases a stack child on its parent's verified tip.
- New overlays: `create-formal-verification-skill` names the explicit-only
  `statechart` skill without slash syntax and reads the report when no chart
  is written. `maintain-formal-verification-skill` makes its deliberate break
  in a disposable checkout. `figure-it-out` runs arena only when a decision
  needs independent candidates.

## Known upstream defects

The Astra review found these in upstream code that this port ships unchanged.
They are left for an upstream fix rather than a port fork:

- `statechart/scripts/run.ts` `joined()` never closes the stdout and stderr
  descriptors it opens, so a model with several broken rules can exit with
  "Too many open files" under a low descriptor limit.
- `watch-pr/github.ts` walks stack parents before it creates its visited set,
  so two same-repository PRs between the same branches in opposite directions
  loop forever.
- `statechart/scripts/test/cli.test.ts` builds its symlink fixture from the
  lexical temporary path, so it fails on macOS when `TMPDIR` is under `/var`.
- Relative `JAVA` and `TLA2TOOLS` paths resolve from statechart's private
  working directory. The overlay requires absolute paths.

No tag, release, deployment, permission change, merge, or user-home
installation is part of this change.
