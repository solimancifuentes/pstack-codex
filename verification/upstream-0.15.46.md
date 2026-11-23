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

- 50 overlay files follow the new upstream text. Eight overlays were retired:
  `architect` and `why` are now host-neutral upstream, and the `how` and
  `reflect` reference prompts and the Orchestrate playbook no longer exist.
- New overlays: `poteto-mode/worker.md` keeps the shared authority boundary. `statechart/SKILL.md` resolves the
  installed skill path and treats the `mise` Java and TLC install and the Pele
  install as explicit dependency setup. Without install authority, it
  requires absolute `TLA2TOOLS` and `JAVA` paths before each run, because the
  command installs Java and TLC whenever its own `mise` lookup fails. It
  treats a `--view` module as code. `ketchup-video` returns the
  video path when the host cannot embed it.
- Every worker kickoff, from any skill, starts with the `worker.md` line,
  except eval candidates and judges, whose briefs carry its rules as plain
  text so blinding holds. The shared contract carries that rule, so standalone
  `how`, `arena`, and `interrogate` runs get it too.
- Inherited roles omit model and effort overrides. Arena substitutes a model
  only when the user's selection allows it. Otherwise it drops the seat, and
  it reports when fewer than two runners remain.
- PRs open ready for review, as upstream opens them. Round 16 removed the
  port's earlier draft-until-verified policy and its landing protocol.
- `reflect` edits pstack through its source overlays, never by copying an
  installed, already-normalized skill into the source tree.
- The packaged launcher `tools/runtime.py` and the shared contract no longer
  offer `orch`; `watch-pr` and `log` remain. The personal manager still runs
  `orch` only when the active release ships it, as v0.1.0 does after a
  rollback.
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
  `7a583913eb1b-e36842559d80` and matches the tracked plugin, `release.json`, the mirrored
  documents, and the repository `NOTICE` and `LICENSE`.
- [All 98 Python tests pass](unit-tests-upstream-0.15.46.txt), including new
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
before the next round. Round 1 led to these changes:

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

Round 2 led to these changes:

- Shipping and Autopilot-full merge with the verified head pinned
  (`--match-head-commit`), wait for checks and reviews that promotion starts,
  and need a fresh verdict when the head moved. Opening a PR passes `--base`,
  using the parent branch for a stack child.
- Autopilot-stack keeps a verdict after a restack only when the parent's change
  cannot affect the PR; an unchanged patch ID alone no longer carries it.
- The shared contract lists the role keys workflows read, including
  `arena runners`, `arena cross-judge pool`, and `interrogate reviewers`.
  `setup-pstack` writes only those keys and treats every value copied from the
  v0.1.0 profile as an old default.
- The arena judge prefers another provider among the models the user
  authorized. Interrogate reports an incomplete review when no adversary
  returns.
- Eval starts candidates and the judge from a fresh context, and reports the
  run as unblinded when the host cannot isolate history.
- `profile set` stores an explicit empty object instead of dropping it.
- Personal skill copies go to `~/.agents/skills/`, the location the manager
  already uses, and the formal-verification handoffs use Codex skill names
  instead of slash commands.

Round 3 led to these changes:

- Every independent seat (arena candidates and judges, interrogate
  adversaries, Comment Sicko, verifiers, eval) starts with no parent history.
  On Codex that is `fork_turns: "none"`, because `spawn_agent` forks the whole
  history by default.
- Shipping gives one merge command on both forges, pinned to the head its
  verdict covers, and arms auto-merge only with that pin. A verdict carries
  across a restack only when the PR's diff is byte-identical, whitespace
  included, and the base change cannot affect it; `git patch-id` alone ignores
  whitespace.
- Checks that start only on ready PRs are expected after promotion, so they no
  longer deadlock a draft. Origin stack children pass `--stack-on`.
- Babysit reads the forge's head, review, and base state before it reports
  merge-ready. Interrogate reports `INCOMPLETE` when no adversary returns.
- The legacy `feature` and `refactoring` keys are documented as read-only
  fallbacks, and `setup-pstack` previews both effects before writing the
  combined key.
- The decision-trail reviewer prefers another provider, the eval judge gets
  the same blinding as candidates, automate-me still finds modes in the old
  `~/.codex/skills/` location, and recipes keep project skill names.

Round 4 led to these changes:

- Opening a PR now defines one draft lifecycle: open, verified draft, promote,
  land. Babysit, Autopilot-full, Autopilot-stack, and Shipping follow it
  instead of each carrying its own draft rules. A verified draft is the report
  a draft gets in place of merge-ready, so Autopilot no longer deadlocks
  before promotion. Checks that start only on promotion are recorded as
  deferred when the repository's triggers show it.
- Landing requires the forge's affirmative mergeable state, rereads head and
  base, and merges with `--match-head-commit` on GitHub or Origin. Shipping no
  longer arms auto-merge, because neither forge documents it as bound to the
  verified head. Origin's documented `--match-head-commit` and `--stack-on`
  flags were checked against its CLI reference.
- `profile set` refuses a profile path inside the installed plugin.
- The decision-trail reviewer inherits history, since it audits the
  transcript. A seat launched with an explicit model reports the requested
  model when the actual one is hidden. `worker.md` carries the eval exception.
- `create-formal-verification-skill` makes its scratch break in a disposable
  checkout, and statechart's coverage is described per broken rule.

Round 5 led to these changes:

- Landing rereads the base repository and branch name as well as the SHAs, so
  a PR retargeted to another branch at the same commit stops. On a branch that
  requires a merge queue, the port enqueues with `expectedHeadOid` instead of
  running `gh pr merge`, which can arm auto-merge when a check is pending. The
  merge method follows what the repository allows.
- Autopilot's verdict comes from the owner's code-ready receipts, and the owner
  reports a verified draft only after it, which removes a circular wait. A PR
  that is already ready skips promotion but still goes through verification
  and landing, and Autopilot-stack can hand it off. Shipping confirms draft
  checks before it promotes.
- Origin reads use `origin pr view --checks`, with `--comments` in Babysit's
  one-pass check.
- The plugin-path guard compares by filesystem identity, so a differently
  cased path on a case-insensitive volume is refused.
- The decision-trail reviewer reports a requested model honestly.

Round 6 led to these changes:

- Autopilot owners send a proof report with head, base, CI, and self-proof
  receipts before the verdict, and report merge-ready or a verified draft only
  after it, which fully removes the circular wait.
- Opening a PR omits `--draft` when a ready PR is requested, turns off an
  already armed auto-merge before promotion or stops for the operator, names
  only the lowest open PR in an Origin merge, and enqueues on a merge-queue
  branch only when the merge-group checks cover the verified behavior.
- Babysit's one-pass check avoids watcher retry backoff, and help text says
  where Babysit stops for drafts.
- The plugin-path guard resolves `..` before comparing, so a sibling path is
  accepted.
- Generated formal-verification skills can read the installed `statechart`
  skill directly, and statechart coverage is described per invariant and per
  temporal property.

Round 7 led to these changes:

- Taking over any PR to babysit or land it first checks for armed auto-merge,
  not only before promotion, so a ready PR cannot land before its verdict.
- Stage 2 is defined by its evidence, so standalone Shipping can verify a PR
  that no agent owns, from its verifier's receipts and the forge's CI.
- Landing accepts GitHub's `UNSTABLE` when every required check and user gate
  passed, and reports the optional failure.
- `gh pr create` gets an explicit title and body, so it runs without a prompt.
  Babysit's direct read also queries review-thread resolution.
- For a model-based check such as TLA+, the formal-verification skills put the
  deliberate break in the model and tie the model to the code with a replay or
  a code-level test.
- Profile and helper-state paths are resolved before writing, so a path
  through a missing directory inside the plugin creates nothing there.

Round 8 led to these changes:

- Takeover also checks merge-queue membership, and dequeues with authority or
  stops.
- Opening a PR pushes the branch first, so creation never prompts, and handles
  repositories that cannot hold drafts by asking before opening ready.
- Stage 2 uses the same required-check and user-gate rule as stage 4, so a
  failing optional check no longer blocks. When the head does not contain the
  current base, the verdict must cover the merge result or a rebased head.
- Babysit's direct GraphQL read selects `isResolved` on each thread node and
  pages through the results.
- Generated formal-verification skills find `statechart` through the skill
  picker or the plugin root a loaded pstack skill gives, never a cache search.
- Profile and helper-state paths are checked for symlinks on every component.

Round 9 led to these changes:

- The merge-result rule applies to the base the verdict ran on; a later base
  move carries the verdict only under Shipping step 3's rule, so landing on a
  busy repository can finish.
- The armed auto-merge check applies only where a verdict gates landing.
  Standalone Babysit reports a user-armed auto-merge and carries on.
- Each required check is classified by its trigger, so a mix of draft and
  promotion-only checks no longer blocks promotion.
- Landings run one per base at a time, and where other writers can move the
  base, the lifecycle relies on the forge's up-to-date rule or a covered merge
  queue, or reports the race.
- Babysit's final read includes the base; Shipping and Autopilot apply the
  required-gate rule when the watcher stops on an optional failure.
- `gh pr create` names the base repository and the pushed head, and Origin uses
  `--status open` for a ready PR.
- Profile and helper-state paths containing `..` are refused for reads and
  writes, so a path always names exactly where it reads and writes.

Round 10 led to these changes:

- `gh pr create` uses `--head <branch>` for a same-repository head and
  `<user>:<branch>` for a user fork, and creates through the REST API with
  `head_repo` for an organization-owned fork.
- Gates that can only clear after promotion, such as code-owner approval, are
  merge gates in stage 4, so they no longer hold a draft back.
- Where other writers can move the base and the forge enforces neither an
  up-to-date branch nor a covered merge queue, landing hands the PR to the
  operator instead of merging.
- Babysit reads required checks directly when the watcher waits on an optional
  check or finds no checks on a ready PR, ends a policy-draft drive when the
  draft's gates settle, and the watcher is pointed at the base repository with
  `--owner` and `--repo`.
- `profile show` follows a symlinked config folder, and the log helper no
  longer needs a helper-state root.

Round 11 led to these changes:

- Every `gh` read and mutation names the PR by canonical URL or with
  `--repo`, and the watcher gets `--owner`, `--repo`, and `--pr`, so a fork
  checkout cannot act on a different PR with the same number.
- Landing rereads the base tip from the branch itself. Instead of handing off
  on every repository without base-freshness rules, it merges, checks the
  merge commit's base parent, and reports and verifies the base branch if the
  base moved in between.
- Optional checks that fail or pend no longer stall Shipping or Origin's
  Babysit drive; required gates are read directly at bounded intervals.
- An Autopilot wording-only change still reruns a lane whose result cannot
  carry forward. The organization-fork REST call sends `draft=true` and the
  right `head` and `head_repo`, and the Origin create command stands on its own.
- Profile writes follow a symlinked config folder and refuse only a symlinked
  target file.

Round 12 led to these changes:

- The post-merge base check finds the landed base per merge method, including
  the first replayed commit's parent for a rebase merge, and confirms the
  merged PR's base branch.
- Babysit takes the base SHA from the branch tip instead of the PR's
  `baseRefOid`, passes `--pr` to the watcher, and its Origin drive also waits
  for unresolved threads.
- Shipping's Origin path polls required gates instead of blocking on
  `origin pr checks --watch`.
- The required set comes from the base branch's rules, so a required check that
  has not reported yet is not mistaken for green.

Round 13 led to these changes:

- The required set is read from the branch the PR finally lands on, through
  two endpoints readable without admin rights, and an empty set passes.
  Shipping uses the same read.
- A required job that skips itself on drafts counts as deferred, never as a
  pass, and every deferred check needs a successful run on the verified
  revision before landing.
- The post-merge check verifies the landed commit by SHA, and for a merge
  queue it confirms that the checked merge group is what landed.
- Babysit runs the thread query in every direct read and reads Origin's base
  tip with `git ls-remote`. Shipping handles upper PRs whose CI runs only
  against trunk. Autopilot-stack owners stop at stage 2.

Round 14 led to these changes:

- A required check that a workflow branch filter keeps from running on a stack
  child is deferred to retarget, so Autopilot-stack hands off instead of
  waiting forever. Babysit reads the required set of the final landing branch.
- A draft-skipped job needs a fresh event, such as reopening the ready PR or a
  new commit; a rerun replays the draft event and skips again.
- On a private repository whose plan has no branch rules, the plan-specific 403
  plus `protected: false` means no required checks. The rules read paginates.
- A merge-queue landing records the tested and landed SHAs separately and
  compares trees when they differ.
- On Origin, Shipping reads back the stack's automatic base move instead of
  retargeting, which could detach the child. Babysit checks every watcher
  `READY` against the required set.

Round 15 (GPT-6.2 Astra and GPT-6.2 Sol; the Opus 5.5 seat could not run
because the account reached its monthly spend limit) led to these changes:

- Babysit compares every ready PR with the final landing branch's required set
  and reports a stack child still on its parent as waiting for retarget.
- A GitHub stack child is created only when the parent's branch exists in the
  target repository; a fork-only parent waits to land first.
- Each deferral records its reason, and after a retarget or promotion a fresh,
  repository-designed skip counts; a draft-guard skip never does.
- `BEHIND` is a separate gate: with authority, update the PR's own branch, wait
  for checks, and reapply the carry rule; otherwise hand off.

Round 16 removed the draft-until-verified policy. Rounds 5 to 15 kept
finding forge edge cases, almost all in the landing protocol that policy
needed: merge queues, jobs that skip drafts, forks, stacked PRs, and strict
branch protection. The findings in rounds 1 to 15 that describe that protocol
no longer apply. Now:

- Opening a PR, Babysit, Shipping, Autopilot-full, Autopilot-stack, and
  `worker.md` follow upstream: PRs open ready, and there is no promotion
  stage. Codex adaptations remain: the runtime contract, host-neutral workers
  started with no parent history, authority to post replies or verdicts, and
  bounded watcher waits.
- These parts of the earlier hardening stay. Merges pin the head the verdict
  covers (`--match-head-commit`), and auto-merge is not armed. A verdict
  carries over only when the PR's diff is identical, whitespace included, and
  under Autopilot-stack only when the parent's change cannot affect it. The
  watcher names the base repository, and Babysit reads the forge's
  mergeable state before it reports merge-ready.
- Stack retargeting on Origin uses upstream's `origin pr edit --base` again.
  Origin's CLI reference returned 404 when round 16 tried to confirm the
  round 14 alternative.

The round 16 review (Claude Opus 5.5, GPT-6.2 Astra, and GPT-6.2 Sol) led
to these changes:

- `gh pr create` passes `--title` and `--body-file` again, because without
  them it fails without a terminal. The Origin command takes the same title
  and body.
- Babysit's `check` mode passes `--max-query-errors 1`, and on Origin it runs
  one `origin pr view --checks --comments`. When the watcher finds no checks,
  as on a repository without CI, Babysit and Shipping read `mergeStateStatus`
  from the forge instead.
- `automate-me` opens its project-skill PR through Opening a PR, so it opens
  ready.
- Autopilot-full pins every merge path to the verified head, and a
  wording-only change reruns any lane the carry rule cannot carry. Shipping
  checks whether a trunk move can affect the patch before landing.
  Autopilot-stack owners send proof receipts without waiting for the
  operator's approval, and the handoff lists that approval.

The round 17 review led to these changes:

- When the watcher finds no checks, Babysit and Shipping also read every page
  of review threads, so an open thread still blocks merge-ready.
- Shipping waits on the frontier PR and merges it itself, because it arms no
  auto-merge. It checks for auto-merge someone else armed before verifying.
  On Origin it leaves a child's parent in place after a merge and syncs the
  stack, as [Origin's stack reference](https://cursor.com/docs/origin/cli/reference/stacks)
  documents.
- A stack child starts from the parent PR's pushed head.
- `automate-me` links Opening a PR. Help no longer promises a reason for
  every skipped step, which upstream dropped, and Bun is required only for
  the watcher.

The round 18 review led to these changes:

- On Origin, Shipping restacks and pushes only the next PR in the run.
  Nothing above the ceiling is rewritten. (Round 19 replaced the commands.)
- Shipping does Babysit's forge read after every watcher `READY`, and merges
  only on the verified head with `CLEAN` or `HAS_HOOKS`. Its final status
  pass checks that every listed PR reads merged, because `--status-only`
  prints a table and never `COMPLETE`.
- Babysit and Shipping read the forge directly when the watcher is not
  prepared.
- Opening a PR pushes and confirms the head SHA before either creation path,
  then checks that the PR's head matches it.

The round 19 review led to these changes:

- Shipping moves the next PR with `git rebase --onto` and pushes only that
  branch with a pinned lease, on both forges. Origin's stack commands are no
  longer used: a review reported that Origin's release notes and stack
  reference disagree on what plain `origin stack push` pushes, and `git fetch
  <trunk>:<trunk>` fails while trunk is checked out in another worktree.
- Shipping reads the forge right before each merge. A head that no verdict
  covers goes back to step 3 at once instead of waiting. Waits have a
  deadline, and the final confirmation reads each PR directly, so it works
  without the watcher.
- Babysit accepts an empty check list as no CI only when the repository runs
  no check for the PR, because GitHub can list none while checks register.
- Autopilot-full owners send self-proof receipts without waiting for a
  forge-required approval, as Autopilot-stack owners already do.
- `reflect` repairs every relative link that leaves a copied skill folder.

The round 20 review led to these changes:

- Shipping's landing and watching steps follow upstream again. Rounds 17 to
  19 had added port rules there, and each round found new defects in them,
  including a wrong rebase boundary for the third PR of a stack. What stays:
  every merge and any armed auto-merge pins the verdict's head with
  `--match-head-commit`, the watcher names the base repository and gets a
  deadline, and on Origin the child's parent is left in place, as Origin's
  stack reference documents. Arming auto-merge, which upstream allows on a
  verified head, is allowed again.
- Babysit's `drive` passes a watcher deadline, and its `check` mode reports
  unregistered checks instead of waiting. Bugbot learnings go to the task's
  decision trail, not the installed reference.
- `reflect` points a copied skill's helper commands at the installed plugin.

The round 21 review led to these changes:

- Shipping falls back to Babysit's direct forge read when the watcher is not
  prepared or finds no checks, and confirms each merged PR directly.
- A new overlay of the Bugbot triage reference sends candidate learnings to
  the task trail instead of the installed file. The port now has 50 overlays.
- Babysit's Origin `drive` re-reads the PR at bounded intervals instead of
  blocking on `origin pr checks --watch`.
- `reflect` edits an existing project or personal copy in place, and copies
  the installed folder only when no copy exists.

The round 22 review led to these changes:

- The Bugbot reference prepares replies, and posts them or resolves threads
  only with authority to communicate on that review, as Babysit requires.
- Babysit's Origin `drive` reads `--comments` too, and its direct GitHub read
  includes `state`, so a merged or closed PR ends the drive.
- `gh pr create` names the base repository, and a fork head is written
  `<owner>:<branch>`.

The round 23 review led to these changes:

- Babysit's `threads-only` mode reads review threads directly instead of
  waiting on the watcher's CI result. When the watcher and the forge
  disagree, `drive` continues with direct reads within the same deadline and
  reports merge-ready only with the forge's agreement.
- Shipping's Origin wait has a deadline.
- An organization-owned fork opens its PR through the REST API with
  `head_repo`.

The round 24 review led to these changes:

- Babysit's watcher rules are split into the watcher, the direct read, and
  the merge-ready test. The watcher passes `--max-query-errors 1`, so a PR
  with no checks reaches the direct read at once, and `drive` runs it in
  slices with a direct read between them, so a pending optional check cannot
  hold the drive. The thread query returns each thread's id, location, and
  comments, so `threads-only` can triage and reply. A branch with no
  required checks passes the required-check test. Shipping's watcher uses the
  same slices.
- Opening a PR offers `origin pr create` for every Origin repository again,
  and limits the REST path to a fork owned by the base repository's
  organization.

The round 25 review (GPT-6.2 Astra and GPT-6.2 Sol; the Opus 5.5 seat
stopped at the account's monthly spend limit) led to these changes:

- Babysit's merge-ready test blocks on `CHANGES_REQUESTED` and reports
  `REVIEW_REQUIRED` as waiting. The forge's merge state decides required
  checks, because `gh pr checks --required` reports only checks that have
  already reported.
- The thread query reads `fullDatabaseId`, because current comment ids
  exceed the deprecated 32-bit `databaseId`.

The round 26 review led to these changes:

- Babysit's merge-ready test no longer accepts `UNSTABLE` for any optional
  check. On a repository without required checks, `UNSTABLE` covers the
  PR's own failing or pending CI, so a pending check always waits and a
  failing one blocks unless it fails the same way on the base or the user
  named it non-blocking. This replaces the round 7 and round 24 rule.
- The direct read rereads the head and merge state after the check and
  thread reads, and repeats the pass if the head moved.
- A reply targets the thread's first comment, which GitHub's reply endpoint
  requires.
- Watcher slices also get a host command timeout, because the watcher can
  finish a read past its own deadline.

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
- The `watch-pr` policy can report `READY` while GitHub shows `BLOCKED`,
  `REVIEW_REQUIRED`, or `BEHIND` for that PR. Babysit now reads those fields
  from the forge before it reports merge-ready.
- `watch-pr` returns `checks-unavailable` for any PR with no checks, such as
  one on a repository without CI, and ends in a `status-query` blocker after
  its retries, dropping the review-thread result. Babysit then reads
  `mergeStateStatus` and the review threads from the forge, and Shipping uses
  Babysit's direct read for its frontier PR.
- Relative `JAVA` and `TLA2TOOLS` paths resolve from statechart's private
  working directory. The overlay requires absolute paths.

No tag, release, deployment, permission change, merge, or user-home
installation is part of this change.
