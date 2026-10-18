# Skill description fidelity repair

A later PR review found that the generator stripped quote delimiters without
decoding YAML escapes. Six descriptions retained literal backslashes before
quotes; `principle-prove-it-works` lost a final apostrophe. All skills loaded,
but models received altered descriptions. Six cases predate the upstream update;
the new formal-verification skill added the seventh.

The generator now decodes JSON-compatible double-quoted YAML scalars, supports
single-quoted scalars with doubled apostrophes, and preserves plain apostrophes.
Unsupported quoted forms fail before rewriting. This keeps the existing
single-line frontmatter scope and adds no YAML dependency. All 49 double-quoted
and six plain descriptions at this pin match a separate PyYAML semantic oracle.

The [package receipt](description-fidelity-package.json) records seven changed
payload headers, unchanged source/adapters/invocation policies, and two identical
exports. Candidate release identity is `0148b78c56c7-5969be8527a3`; its local ZIP
SHA-256 is `db7fa82abb11b881e2b48a0541198e202da4702213b1c84aa860e5fd4714326b`.
Earlier cloud receipts describe the preceding candidate and remain historical.

All [85 Python tests pass](description-fidelity-python-tests.txt). Six new tests
fail against the earlier parser and pass after repair. They cover real formal
trigger text, quote/backslash/Unicode decoding, trailing apostrophes,
normalization idempotence, and unsupported input leaving files unchanged.

The [native receipt](description-fidelity-native.json) records a real Codex CLI
0.159.2 install and fresh app-server discovery in task-only child state. All 55
native descriptions equal their semantic effective source, generated header,
and manifest. It includes per-description SHA-256 comparisons. All 205 cached
payload files match, no parse errors occur, and no credentials were copied or
`auth.json` created. The intentional unslop suffix remains. Native lifecycle,
Bun, TypeScript and bounded workflow evidence for the preceding candidate is in
[the cloud validation record](cloud-validation-upstream-0.15.27.md); runtime and
helper code are unchanged by this repair. No release or tag was published.
