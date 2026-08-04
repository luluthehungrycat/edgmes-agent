## Why

Transcript-heavy prompts waste scarce context on constrained edge models and make continuity fragile. Edgmes needs a bounded projection of durable facts, current goal, evidence, actions, artifacts, and verification state while retaining the raw transcript for audit and later reconstruction.

## What Changes

- Add immutable state-ledger entries for durable, task-relevant state.
- Add deterministic context-item selection under a character/token budget.
- Preserve priority, recency, and verification metadata in the bounded projection.
- Keep raw transcript storage outside the model-facing projection.
- Reject oversized or malformed ledger entries instead of silently exceeding the budget.

## Capabilities

### New Capabilities

- `state-ledger`: Structured bounded state for continuity across turns and fresh processes.
- `bounded-context-selection`: Deterministic selection of relevant ledger and task items within a model budget.

### Modified Capabilities

- None.

## Impact

- New side-effect-free interfaces under `edgmes/`.
- Focused tests and documentation.
- No changes to inherited transcript persistence or Hermes runtime behavior.
