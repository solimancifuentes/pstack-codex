### Pause safely

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.** This is explicit only. On "keep going", "going to bed, keep going", or "don't stop", continue within actual runtime limits. Compaction continues the same task; it is not a user-requested pause. A runtime limit warrants a truthful checkpoint rather than a false persistent-run promise.

1. Stop at a safe boundary. Finish the current atomic step or back out of it. Start nothing new, and cancel any nested subagents.
2. Take no irreversible action to pause. No PR and no push unless you already had one out.
3. Make the work durable. Preserve this run's uncommitted work. If a checkpoint commit is appropriate, stage only the owned paths and use a clear `wip:` commit on the owned branch. Do not commit unrelated user changes. If the tree is broken, say so in the commit body in one line.
4. Write the resume note off-context. Capture intent, what you were doing, progress and what's verified, current state, next steps, key files, and gotchas. Before an unavoidable runtime boundary, write it to a durable allowed path such as `work/pstack/<slug>/resume.md`. Compaction alone does not stop the task. If a show-me-your-work trail exists, point at it instead of duplicating it.

**Reply:** where you are in the loop, what's on disk versus still in your head (paths, no diff dumps), the commits you made and whether the tree is clean, and the first action on resume. This is a pause, not a final report.
