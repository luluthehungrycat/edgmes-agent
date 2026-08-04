## 1. Package boundary

- [x] 1.1 Include `edgmes` packages in setuptools discovery and expose the `edgmes` console entry point.
- [x] 1.2 Add a source boundary checker for forbidden upstream imports, Hermes-home references, and manifest omissions.
- [x] 1.3 Add focused tests for passing and failing boundary fixtures.

## 2. Upstream synchronization

- [x] 2.1 Add deterministic upstream-only changed-path classification with protected-path risk labels.
- [x] 2.2 Add explicit branch creation and no-automatic-merge behavior.
- [x] 2.3 Document remote, branch, conflict, and review expectations.

## 3. Edge CI

- [x] 3.1 Add path-scoped edge CI for boundary checks, focused tests, compilation, and lint.
- [x] 3.2 Add scheduled/manual sync workflow that creates a PR and never writes directly to `main`.
- [x] 3.3 Verify locally and with remote CI.
