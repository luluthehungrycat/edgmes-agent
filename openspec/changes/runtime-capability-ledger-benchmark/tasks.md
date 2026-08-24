## 1. OpenSpec and profile foundation

- [x] 1.1 Add the named profile registry and conservative preset definitions while preserving the legacy default profile.
- [x] 1.2 Extend runtime requests and results with explicit profile/policy inputs and policy metadata.
- [x] 1.3 Enforce profile resolution, required/optional capability and tool checks, budgets, step/tool-call limits, and mutation approval before backend invocation.
- [x] 1.4 Add profile catalog, precedence, rejection, and backend-not-called regression tests.

## 2. Ledger runtime integration

- [x] 2.1 Add versioned JSON serialization, strict loading validation, and atomic persistence for immutable ledger snapshots.
- [x] 2.2 Correct context projection accounting so the measured budget matches rendered backend context and omission metadata remains deterministic.
- [x] 2.3 Make runtime turns update the in-memory ledger and optionally persist it across fresh processes, including safe failure/verification records.
- [x] 2.4 Add persistence, reload, budget, secret-safety, and multi-turn runtime regression tests.

## 3. Verification benchmark

- [x] 3.1 Define the versioned six-case benchmark model, executor protocol, metric schema, and isolated fixture lifecycle.
- [x] 3.2 Implement deterministic inspect, diagnose, edit, test, recovery, and safe multi-step fixture cases with explicit postconditions.
- [x] 3.3 Implement machine-readable JSON output, aggregate summaries, timeout/failure handling, and executor/model metadata.
- [x] 3.4 Add the benchmark CLI and tests proving fixture isolation, metric completeness, reproducibility, and destructive-action avoidance.
- [x] 3.5 Document benchmark usage, limitations, and how to run an explicitly configured local-model executor.

## 4. Integration documentation and verification

- [x] 4.1 Update the Edgmes roadmap and runtime/benchmark documentation to reflect the implemented profile, ledger, and benchmark contracts.
- [x] 4.2 Run focused Edgmes tests, lint, compile checks, the benchmark self-run, and the full available repository test runner.
- [x] 4.3 Validate `runtime-capability-ledger-benchmark` with OpenSpec strict validation and confirm all artifacts are complete.
