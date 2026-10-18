# Upstream pstack 0.15.27 update

This checkout prepares unpublished port 0.2.0. Published installations remain on
v0.1.0 until a reviewed port release is available.

## Source identity

The fork baseline is `9d2841a9c318bf78ebc25b1eb1e78ac0b6c5c2bd`, port 0.1.0.
It pins upstream pstack 0.15.25 at
`850d7f2e9f5e55dff7eb00a0a479337fe79eb22f`.
The update pins [pstack 0.15.27 at
0148b78c56c72a1b8412055913c79f767095b217](https://github.com/cursor/plugins/commit/0148b78c56c72a1b8412055913c79f767095b217).
Both upstream plugin manifests report 0.15.27. The upstream repository has no
GitHub releases or version tags. This identity comes from its versioned source.

The [referenced X announcement](https://x.com/poteto/status/2111926622278521253)
was verified in a signed-in cloud browser by the coordinating task. It announces
pstack v0.15.27 and the beta `create-formal-verification-skill`, matching this
source pin. This worker's direct HTTP request returned 403; browser verification
was provided separately. Official upstream source remains the basis for the
imported files.

Source acquisition used `git archive` from a fresh clone of
`https://github.com/cursor/plugins.git` at the exact commit. The source manager's
HTTP fetch hit a proxy 403. All 171 imported source files match the official Git
tree byte for byte. The [delta](upstream-0.15.27-delta.json) contains 29 changed
files and two additions, with no removals. Executable bits on unchanged archived
helpers retain this repository's existing modes.

## Behavior and adaptations

- Adds [create-formal-verification-skill](https://github.com/cursor/plugins/pull/709).
  It selects a verification method for a specific code property, records bounds
  and counterexamples, tests a broken variant, and preserves real findings.
  The port now has 55 skills. The new skill remains explicit-only.
- Ketchup keeps every pending decision with enough context to act. Sharpen drops
  its ban on returning a rewritten prompt. Review, root-cause, premise-testing,
  idempotency, migration, behavior-testing, and TypeScript guidance follow upstream.
- Four upstream changes overlap adapters. Poteto-help gains the new skill and
  ketchup wording. Poteto-mode gains three updated principle summaries and its
  normalized name. Make-bot-ui gains its normalized name. Swarm drops repeated
  prose while retaining Codex capacity and runtime rules.
- The complete poteto-mode workflow remains progressively loaded. All 23 playbooks,
  24 principles, Codex and Dots adapters, permission boundaries, external user
  preferences, explicit helper setup, and original MIT attribution remain.
- The new Claude Code guide is retained only in the upstream source archive.
  It does not become an operating instruction for the Codex package.

## Verification

The [baseline run](baseline-tests-before-0.15.27.txt) and
[updated run](unit-tests-upstream-0.15.27.txt) each pass all 70 Python tests.
The suite covers reproducible builds and ZIP export, contained Markdown links,
metadata and invocation policy, profile preservation, update/rollback recovery,
and helper runtime boundaries. Lifecycle tests simulate native installation.

`python3 source/tests/verify_repository.py` rebuilds the source and compares the
tracked plugin, release manifest, and mirrored distribution docs. The
[package receipt](upstream-0.15.27-package.json) records the result. It also fails
on a scratch export with modified formal-verification skill content and passes
again after restoration. The [integrity receipt](export-integrity-upstream-0.15.27.json) records the failure, restoration, and two byte-identical exports.
The ZIP is local verification output only.

Initial discovery against the configured read-only home failed. Subsequent
[cloud validation](cloud-validation-upstream-0.15.27.md) used documented child-only
Codex state roots and verified actual native install, update, rollback,
remove/reinstall, exact loader identities, Bun helpers, and representative
workflows. All 79 Python tests and 68 Bun tests pass; strict TypeScript checking
passes. The discovered harness identity bug is fixed with nine regression tests.
The newer validation record supersedes the earlier native-discovery and absent-Bun
limits while preserving their historical receipts.

No tag, release, deployment, permission change, merge, credentials installation,
or agent-hub update is part of this branch.

Two [independent review passes](review-upstream-0.15.27.json) found no blocking
issues. Both inherited the parent model; exact model identity was unavailable.
This is same-provider review, without cross-provider assurance. One redundant
script docstring was removed after comment review.
