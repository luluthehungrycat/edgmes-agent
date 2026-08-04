## 1. Edgmes home isolation

- [x] 1.1 Add an Edgmes home-path resolver with `EDGMES_HOME` override and `~/.edgmes` default
- [x] 1.2 Add deterministic config, state, sessions, skills, cache, logs, and runtime path accessors
- [x] 1.3 Add tests for default home, absolute override, invalid override, Hermes isolation, and explicit initialization

## 2. Profile and routing contracts

- [x] 2.1 Add immutable specialist profile metadata and registry validation
- [x] 2.2 Add route decision, policy error, and bounded specialist handoff data types
- [x] 2.3 Add deterministic classifier interface with abstention and confidence thresholds
- [x] 2.4 Add routing coordinator with explicit, deterministic, local-router, escalation, and unresolved precedence
- [x] 2.5 Add tests for unknown profiles, bounded toolsets, routing precedence, invalid output, escalation, and policy rejection

## 3. FunctionGemma-compatible local routing

- [x] 3.1 Add an optional local-router protocol that has no model-runtime dependency
- [x] 3.2 Add strict parsing and validation for FunctionGemma-style structured route output
- [x] 3.3 Add mocked adapter tests for valid, malformed, unavailable, and low-confidence local routing
- [x] 3.4 Verify the local router cannot invoke escalation or expand profile capabilities

## 4. Verification and documentation

- [x] 4.1 Add package-boundary tests proving the new modules do not import Hermes runtime internals
- [x] 4.2 Run focused Edgmes tests, OpenSpec validation, and Python syntax checks
- [x] 4.3 Document the routing contract, `~/.edgmes` layout, and future runtime integration seam
