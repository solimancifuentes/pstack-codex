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
413 files, changes 82, and removes 31. 410 of the added files belong to the new
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

- 46 overlay files follow the new upstream text. Eight overlays were retired:
  `architect` and `why` are now host-neutral upstream, and the `how` and
  `reflect` reference prompts and the Orchestrate playbook no longer exist.
- New overlays: `poteto-mode/worker.md` keeps the shared authority boundary and
  the port's draft-until-verified PR policy. `statechart/SKILL.md` resolves the
  installed skill path and treats the `mise` Java and TLC install and the Pele
  install as explicit dependency setup.
- The `orch` helper is removed from `tools/runtime.py`, the manager, the shared
  contract, and the tests. `watch-pr` and `log` remain.
- The default arena and interrogate panels have three seats, matching
  upstream's panel size. The `architect` panel default is gone. Existing
  profile keys are preserved, and `setup-pstack` reports retired roles.
- The build lint now also rejects `claude-fable-5-2-` and `gemini-4-neon-`
  slugs in packaged skills, as it already did for Opus and Grok slugs.
- Codex and Dots adapters, external preferences, explicit invocation policy,
  and MIT attribution are unchanged.

## Verification

- `python3 source/tests/verify_repository.py` rebuilds release
  `7a583913eb1b-804afab2ccef` and matches the tracked plugin, `release.json`,
  and mirrored documents.
- [All 85 Python tests pass](unit-tests-upstream-0.15.46.txt). They cover
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
- `statechart` was not run against TLC, and its own test suite did not run.
  Java, TLC, and its `fast-check` test dependency were not installed.
- No independent review of the adapted text has run yet.

No tag, release, deployment, permission change, merge, or user-home
installation is part of this change.
