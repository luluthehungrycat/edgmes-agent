## Context

The capability policy layer now provides resource limits but does not choose which continuity state enters a prompt. The new ledger and selector remain side-effect-free seams until the edge runtime integrates them.

## Goals / Non-Goals

**Goals:**

- Represent structured continuity state with bounded immutable entries.
- Select deterministic model-facing context under a character budget.
- Prioritize current request, verified state, and high-value evidence.
- Keep raw transcript persistence and provider integration unchanged.

**Non-Goals:**

- Replacing Hermes transcript/session storage.
- Summarizing text with an auxiliary model.
- Tokenizer-specific accounting or model inference.
- Automatic deletion of durable state.

## Decisions

### Use immutable value objects

Frozen dataclasses make state safe to pass between selectors and runtimes, and make repeated selection reproducible. The ledger itself is a snapshot rather than a mutable database.

### Rank before packing

A deterministic sort by mandatory status, verification, priority, recency, and stable identifier makes selection explainable and testable. A greedy packer then includes whole items only, avoiding partial prompt fragments.

### Budget serialized text, not guessed tokens

The first seam uses a caller-provided character budget, which is portable and deterministic without a tokenizer dependency. Later runtime integration can translate model token budgets into conservative character budgets.

### Keep raw history outside the projection

The transcript remains available to persistence and audit layers, but selector inputs are structured entries only. This prevents accidental prompt inflation and reduces injection surface.

## Risks / Trade-offs

- [Risk] Character budgets are an approximation of tokens → use conservative conversion in runtime integration.
- [Risk] Greedy selection can omit useful lower-ranked combinations → expose ranking metadata and add smarter selection only after benchmark evidence.
- [Risk] State may become stale → retain recency and verification fields so later policy can expire or refresh entries.

## Migration Plan

Add interfaces alongside current Hermes persistence. No migration or data rewrite occurs. The edge runtime will explicitly construct snapshots and projections when it is introduced.
