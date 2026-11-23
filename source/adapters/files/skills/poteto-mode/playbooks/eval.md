### Eval

Read the [shared runtime contract](../../../CODEX.md) for delegation, authority, models, history, helpers, and session limits.

**You own the experiment design. Plan, blind, run, synthesize.**

**Non-negotiables for blinding:**

- No `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, or `arena` in any directory, file, or prompt the candidate sees.
- The candidate prompt looks like an organic user request. State the goal, not the meta.
- No chain-eliciting cues. Don't ask the candidate to list which skills, principles, or files they applied. Ask for design notes generally and grade chain-following from code shape, not self-report.
- Sanitize directory and slug names. Use project-shaped names a user might pick.
- Candidates are not implementation delegates. Do not give them the `worker.md`, `poteto-agent`, or poteto-mode paths, which name the workflows under test. Put the authority and isolation rules from `worker.md` into the brief as plain text instead.
- Start every candidate and the judge with a fresh context that holds only its brief, never a fork of the coordinator's conversation, for example `fork_turns: "none"` where the spawn tool supports it. The coordinator's history holds the rubric and the label-to-model mapping. If the host cannot isolate history, report the eval as unblinded.
- Don't tell the candidate other candidates exist.
- The judge can know it's judging but sees outputs by sanitized label only, never by model name.
- Comparing two variants: one judge scores both sets in a single pass on one scale, blind to which set each came from.

**Steps:**

1. **Frame.** State what variant is under test and what behavior counts as success. Write the rubric (3-6 concrete criteria) for the judge only. Hold it back from candidates.
2. **Set up sanitized environments.** Per-candidate working dir with the variant in place. Plant any context an organic task would have: a project skeleton, the skills the candidate would naturally read.
3. **Author one organic prompt.** What a user would type. No leakage of what's being measured.
4. **Spawn N independent candidates** under the actual runtime model policy per the **arena** skill's Phase B. Each works in its own sanitized dir. Same prompt to each. Follow the actual model and delegation policy in CODEX.md. An agent that only dispatches, polls, or packs results can run at a lower reasoning level only when the user's selection for that role permits it.
5. **Spawn one blinded judge** that authored no candidate, using an explicitly authorized different model when available and recording same-provider limits otherwise per the **arena** skill's Phase C. Judge sees outputs by sanitized label and the rubric, never a model name.
6. **Verify observed actions, not self-report.** Read explicitly scoped candidate traces when available, plus the files each actually produced. Chat summaries do not prove which files a candidate opened. If complete traces are unavailable, mark chain-following evidence incomplete and grade only observable artifact behavior. Do not search unrelated private chat directories.
7. **Read every candidate output yourself** end to end. Compare to the judge's verdict. Disagreement means a model is biased or the rubric is ambiguous. Synthesize.

**Reply:** variant under test, rubric, per-candidate notes, judge's verdict, your synthesis, and a recommendation for whether to promote the variant.
