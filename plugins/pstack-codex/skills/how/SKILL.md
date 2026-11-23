---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions.

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

## 1. Explain

Launch one independent host-native delegate with a read-only assignment that explores and explains in one pass, under the delegation and model policy in [CODEX.md](../../CODEX.md). It inherits the parent's model settings by default. Read-only is an instruction boundary, not a restricted tool sandbox. If delegation is unavailable, explore and explain directly and say so. Give it the user's question and this brief:

> You are writing an architectural explanation for a senior engineer. Explore the codebase and write an explanation that a senior engineer unfamiliar with this area could read and walk away with a solid mental model. They should understand the architecture well enough to start working in it confidently. You have read-only access to the codebase.

## 2. Present

Present the delegate's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.
