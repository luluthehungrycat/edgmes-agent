## 1. OpenSpec and measurement contracts

- [x] 1.1 Add tokenizer measurement protocol and validated measurement result metadata.
- [x] 1.2 Define conservative fallback and exact rendered-context accounting.
- [x] 1.3 Add requirements and tests for 16K, 32K, 48K, and 64K budgets.

## 2. Deterministic compaction

- [x] 2.1 Add pure compaction/projection API over immutable ledger entries.
- [x] 2.2 Preserve mandatory current request and verified state; fail closed when mandatory context cannot fit.
- [x] 2.3 Return stable omission reasons and prove repeated compaction is identical.

## 3. Runtime integration

- [x] 3.1 Integrate measured budgeting into `EdgeRuntime` without changing `ChatBackend`.
- [x] 3.2 Preserve character-budget compatibility when no tokenizer is configured.
- [x] 3.3 Add focused tests, docs, compile/lint checks, and strict OpenSpec validation.
- [ ] 3.4 Run the Edgmes benchmark and record whether the executor used exact or fallback accounting.
