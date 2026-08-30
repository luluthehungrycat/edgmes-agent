## Context

`edgmes.ledger.select_bounded_context` currently packs whole entries by rendered character length. `EdgeRuntime` subtracts its system prompt and sends the resulting projection to the backend. The next seam must improve accounting without making tokenizers mandatory or changing provider protocols.

## Decisions

### Tokenizer seam

Define a small callable/protocol that accepts rendered text and returns a positive token count. Tokenizer failures, unavailable adapters, and invalid counts use a documented conservative character fallback. The adapter is injected into budgeting APIs; no model-name heuristic or network lookup is used.

### Budget invariant

The measured text is exactly the text sent to the backend. A projection is valid only when its measured count is at or below the active budget. The system prompt and rendered ledger projection are measured together, not independently.

### Compaction

Compaction is a pure operation over immutable entries. It uses the existing deterministic ranking, preserves all mandatory entries or fails closed, and returns selected entries plus stable omission metadata. It never mutates the source ledger or silently truncates an entry.

### Compatibility

Character budgeting remains the default when no tokenizer is supplied. Existing callers and the provider-neutral `ChatBackend` protocol remain compatible. Artificial budgets of 16K/32K/48K/64K are test fixtures, not model capability claims.

## Risks

- Tokenizer counts can differ from a provider's final serialization; document that adapters must model the backend's serialization.
- Conservative fallback may omit useful context; report the fallback mode and omission reasons.
- Compaction can discard relevant history; preserve mandatory/verified ranking and expose the complete omitted IDs.
