## 1. Capability contracts

- [x] 1.1 Add immutable model capability profile and registry contracts under `edgmes/`.
- [x] 1.2 Validate profile identifiers, positive budgets, tool identifiers, and secret-like metadata rejection.

## 2. Pure policy resolver

- [x] 2.1 Add immutable policy request and decision contracts.
- [x] 2.2 Implement deterministic capability/tool intersection with required-versus-optional handling.
- [x] 2.3 Enforce context, output, step, tool-call, and mutation approval limits without side effects.
- [x] 2.4 Export the public contracts from `edgmes`.

## 3. Verification and documentation

- [x] 3.1 Add focused tests for valid boundaries, filtering, rejection, immutability, and secret safety.
- [x] 3.2 Document capability profiles and policy resolution for future edge-runtime integration.
- [x] 3.3 Run focused tests, compilation, OpenSpec strict validation, and diff checks.
