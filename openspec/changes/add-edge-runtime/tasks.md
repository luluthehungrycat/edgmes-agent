## 1. Runtime contracts

- [x] 1.1 Add backend protocol, runtime request/result, and structured runtime errors.
- [x] 1.2 Compose capability policy and bounded ledger context before backend access.

## 2. Local backend and entry point

- [x] 2.1 Add dependency-free Ollama HTTP adapter with timeout and response validation.
- [x] 2.2 Add `python -m edgmes.runtime` one-shot CLI entry point.
- [x] 2.3 Record response/verification state in a new immutable ledger snapshot.

## 3. Verification

- [x] 3.1 Add fake-backend tests for allowed, rejected, bounded-context, and ledger-update paths.
- [ ] 3.2 Run a real local Ollama smoke task and capture verifiable output.
- [x] 3.3 Run full Edgmes tests, compilation, lint, strict OpenSpec validation, and diff checks.
