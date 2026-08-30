## Why

Edgmes currently bounds rendered context by characters. That is deterministic and dependency-free, but it cannot enforce a model's actual token window and has no explicit compaction contract.

## What Changes

- Add an optional tokenizer adapter and observed token-count contract.
- Keep a conservative deterministic fallback when no tokenizer is available.
- Enforce budgets against the exact rendered backend context, including system text and separators.
- Add deterministic compaction that preserves mandatory current-request and verified state before lower-value history.
- Validate artificial 16K, 32K, 48K, and 64K budgets without requiring a heavyweight dependency.

## Capabilities

### New Capabilities

- `context-budgeting`: Convert profile budgets into exact or conservative bounded context projections.
- `deterministic-compaction`: Reduce ledger/context candidates reproducibly while preserving mandatory state and omission reasons.

## Impact

Affected code: `edgmes/ledger.py`, `edgmes/runtime.py`, optional tokenizer adapter module, tests, and Edgmes documentation. The default runtime remains standard-library-only and provider-neutral.
