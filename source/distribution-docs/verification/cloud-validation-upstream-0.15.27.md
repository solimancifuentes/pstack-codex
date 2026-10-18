# Cloud validation of the pstack 0.15.27 update

The repository update passes the executable cloud checks below. The draft PR is
ready for coordinating review. No tag or release was created.

## Native install, update and rollback

Codex CLI 0.159.2 supports a documented `CODEX_HOME` override for users and tests.
Each child process used a fresh task-only directory for that intended purpose.
The caller's environment and configured read-only home were unchanged. No
credentials were copied or installed, and no app-server code or permissions
were changed. The original home-startup failure is historical evidence, not a
remaining native CLI discovery blocker.

The [native lifecycle receipt](native-lifecycle-upstream-0.15.27.json) records real
CLI installation of v0.1.0, update to 0.2.0, rollback to v0.1.0, and restoration to
0.2.0. Each installed cache matched its release payload byte for byte. Separate
fresh native app-server processes discovered exactly 55, 54, and 55 enabled
plugin skills after update, rollback, and restoration, with no parse errors.
Exact skill identities matched each phase's release manifest.

The [remove/reinstall receipt](native-remove-reinstall-upstream-0.15.27.json)
records removal, zero discovered plugin skills, expected harness rejection of
the removed plugin, reinstall, and 55 discovered skills. Fixture profile bytes
survived every native lifecycle step. No `auth.json` was created.

An [installed-cache workflow](native-cache-workflow-upstream-0.15.27.json) ran the
actual packaged launcher. It preserved unknown fields during a confirmed
scratch profile update and read persisted orchestration state through Bun.
This exercises the native-installed payload directly, separately from loader
discovery. It does not claim a new authenticated native CLI model conversation.

The optional personal manager deliberately rejects custom native homes.
Its [scope preflight](manager-scope-preflight-upstream-0.15.27.json) rejected the
alternate-home install before creating that directory. Its separate
[filesystem lifecycle simulation](managed-lifecycle-simulation-upstream-0.15.27.json)
uses the actual old and new packages with the existing `NativeFixture`, preserving
profile bytes and unrelated marketplace entries through 54/55/54 skills and
uninstall. This simulation is not the real native CLI proof above.

## Corrected discovery verification

The first native run exposed a harness defect. A broad path substring match
counted five built-in system skills because the task directory contained the
repository name. The harness now selects exact native plugin IDs, requires
installed/enabled state, handles repeated observations, and rejects conflicting
paths. `--expected-manifest` verifies every expected qualified skill name.

Nine regression tests cover this change. The original captured v0.1.0 response
passes with 54 exact identities against v0.1.0, and fails against 0.2.0 even
without a count check because the new formal-verification skill is missing.
All [79 Python tests pass](python-tests-after-discovery-fix.txt).

## Bun and representative workflows

Bun 1.4.3, revision `1.4.3+c6da4a4d3`, came from the official
`@oven/bun-linux-x64@1.4.3` npm vendor package. npm verified its registry integrity;
installation used `--ignore-scripts` and task-only paths. The packaged launcher
prepared its locked dependencies with `--frozen-lockfile --ignore-scripts` in
external mutable state. The immutable plugin payload stayed unchanged.

All [68 Bun tests pass](bun-tests-upstream-0.15.27.txt), and
[strict TypeScript checking passes](typecheck-upstream-0.15.27.txt).
Actual launcher commands created and updated a scratch work unit, read it in a
fresh process, recorded and read its verification verdict, displayed watcher
help without a live GitHub query, and escaped formula-like log input. The same
prepared helpers worked across the actual old/new package simulation.

A worker used the new formal-verification skill on actual profile-update code.
The [bounded verification receipt](formal-workflow-upstream-0.15.27.json) records
48 concrete inputs and all six two-writer read/replace orders. The documented
serial preservation property passes all 96 serial traces. A shallow-merge
scratch mutation fails 64 serial traces; restoration returns to 96 passes.
A separate actual serial CLI update preserves nested unknowns and `unslop=false`.

The stronger concurrent-writer extension fails 192 overlapping traces. Both
writers can read an old profile, then the second whole-file replacement loses
the first writer's disjoint update. This is a retained preexisting concurrency
risk, not a documented guarantee or an update regression. The runtime source is
unchanged. The workflow reports `ISSUES` for this finding even though its outer
acceptance driver succeeds. It is not a proof for arbitrary JSON, crashes, I/O
failures, path races, or the whole runtime.

## Scope of readiness

The source update, reproducible package, native CLI lifecycle and loader,
helper runtime, and representative direct workflows are verified in this cloud
environment. The temporary environment had a transient transport disconnect;
subsequent command execution and native CLI checks established reconnection.

Publication remains outside this task's authority. A future release needs its
release metadata, installation tag instructions, and publication checks
finalized under that separate scope. Desktop UI and live Dots remain outside
this Linux cloud environment; their existing experimental compatibility limits
still apply. The advanced personal manager's real-home native integration is
unexercised because its explicit guard excludes this isolated setup. No result
above claims otherwise.

Official references: [Codex home resolution at 0.159.2](https://raw.githubusercontent.com/openai/codex/rust-v0.159.2/codex-rs/utils/home-dir/src/lib.rs),
[plugin cache roots](https://raw.githubusercontent.com/openai/codex/rust-v0.159.2/codex-rs/core-plugins/src/store.rs),
and [Bun installation](https://bun.com/docs/installation).

An [independent final review](review-cloud-validation-upstream-0.15.27.json)
recomputed native identities, cache hashes, bounded trace results, and regression
tests. It found no actionable issues. The reviewer inherited the parent model;
exact model identity was unavailable. No cross-provider assurance is claimed.
