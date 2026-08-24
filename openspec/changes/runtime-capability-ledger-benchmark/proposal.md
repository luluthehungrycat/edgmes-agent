## Why

Edgmes already has pure capability-policy and bounded-ledger primitives, but the runtime currently exposes only one hard-coded profile and one-shot state behavior. It needs an enforceable profile-driven execution path, durable bounded continuity, and a reproducible benchmark before it can demonstrate the project’s first usable-release contract.

## What Changes

- Add named capability profiles for the supported edge tiers and resolve a profile before backend request construction.
- Make runtime tool exposure, budgets, step limits, and mutation approval policy enforceable at the public runtime boundary.
- Integrate the state ledger into runtime turns, including bounded context projection, completion/verification records, and persistence across processes.
- Add tokenizer-aware or explicitly documented budgeting/compaction seams without allowing context to exceed the active profile budget.
- Add a versioned verification benchmark covering representative read-only, diagnostic, mutation, recovery, and safe multi-step tasks.
- Record benchmark results for completion, invalid/unnecessary tool calls, context growth, recovery, verification, latency, and destructive-action avoidance.

## Capabilities

### New Capabilities

- `runtime-capability-profiles`: Enforce named model capability contracts at the Edgmes runtime request boundary.
- `bounded-state-ledger`: Carry verified, secret-safe, bounded continuity state across runtime turns and fresh processes.
- `verification-benchmark`: Execute and report a reproducible suite of representative Edgmes tasks and safety/quality metrics.

### Modified Capabilities

- None.

## Impact

- Affected code: `edgmes/runtime.py`, `edgmes/capabilities.py`, `edgmes/ledger.py`, CLI/runtime adapters, and new benchmark modules/tests.
- Affected documentation: Edgmes roadmap and benchmark usage documentation.
- Dependencies: prefer the existing standard-library runtime and locked development environment; tokenizer support must be optional or isolated so the edge runtime remains lightweight.
- The existing injected `ChatBackend` protocol remains provider-neutral. Existing callers that use the default one-shot runtime retain conservative behavior, while new profile/ledger options become explicit runtime configuration.
