## Context

See `proposal.md` for motivation and scope. `edgmes.capabilities` already provides immutable profiles and a pure policy resolver; `edgmes.ledger` already provides immutable entries and deterministic bounded selection; `edgmes.runtime` currently wires one default profile and returns a ledger snapshot but does not expose a profile catalog, persist state, or provide the six-case verification benchmark.

## Goals / Non-Goals

**Goals:**

- Make profile selection explicit, named, and enforced before backend invocation.
- Make ledger continuity real across runtime calls and fresh processes while preserving secret rejection and deterministic selection.
- Provide a deterministic benchmark harness with isolated fixtures and machine-readable results, plus an optional injected executor seam for real local-model runs.
- Preserve the provider-neutral backend protocol and conservative default behavior.
- Keep OpenSpec requirements, tests, roadmap, and usage documentation synchronized.

**Non-Goals:**

- Replacing the inherited Hermes conversation loop.
- Adding executable tools to the Edgmes runtime in this change.
- Claiming benchmark results represent model quality when using the deterministic fixture executor.
- Introducing a mandatory tokenizer or heavyweight runtime dependency.
- Building a production scheduler, database, or multi-user ledger service.

## Decisions

### Profile registry and request precedence

Add a deterministic default profile registry containing `nano`, `small`, `medium-edge`, `full`, and the legacy-compatible `edge-small` profile. `EdgeRuntime` resolves the request profile first, then falls back to its configured default profile; explicit request values therefore override runtime defaults. The existing pure resolver remains the single policy authority. Alternatives considered: model-name heuristics were rejected because model names do not prove observed capability; a mutable global registry was rejected because policy snapshots must be immutable and testable.

### Runtime request and backend boundary

Extend the public runtime request with profile ID and policy inputs (required/optional tools and capabilities, requested steps/tool calls, mutation approval). The runtime constructs no backend request until resolution succeeds. The backend protocol remains unchanged for this one-shot slice; permitted tools are represented in policy/result metadata rather than silently executed. Alternatives considered: changing every backend signature was rejected as unnecessary provider coupling.

### Ledger persistence format

Add a JSON object representation with a format version, ordered entries, and explicit fields. `StateLedger.save` writes atomically through a temporary sibling file and `StateLedger.load` validates the entire representation through the existing constructors. Persistence is optional and activated by a runtime ledger path. Alternatives considered: pickle was rejected for safety; SQLite was rejected as unnecessary for immutable snapshots and would add a dependency/operational surface.

### Context accounting

Keep character budgeting as the stable dependency-free contract, but make the measured serialized projection equal the text sent to the backend, including category labels and separators. A tokenizer adapter can be added later without changing the ledger API. Alternatives considered: silently estimating tokens was rejected because it would make the current budget unverifiable.

### Benchmark architecture

Create a versioned benchmark module with six declarative cases, isolated temporary fixtures, a deterministic reference executor, and an injectable executor protocol for local-model adapters. Each result is JSON-serializable and records status, metrics, evidence, and failure reason. The default command is offline and reproducible; real model runs are explicitly labeled by model/configuration. Alternatives considered: invoking a live model by default was rejected because network/model availability would make CI nondeterministic.

## Risks / Trade-offs

- [Risk] Character budgets differ from provider token budgets → Mitigation: document the contract and keep tokenizer integration as an explicit future seam.
- [Risk] Persisted files may be corrupted or replaced → Mitigation: versioned schema, strict validation, atomic writes, and fail-closed loading.
- [Risk] The deterministic benchmark may overstate real model performance → Mitigation: label executor type and report it in every result; use live adapters only as explicit runs.
- [Risk] Profile presets could imply unsupported model abilities → Mitigation: treat presets as limits, not capability discovery, and require explicit model/profile selection for non-default tiers.
- [Risk] Existing callers depend on the current `RuntimeResult` shape → Mitigation: preserve existing fields and add compatible optional configuration/results only.

## Migration Plan

1. Add profile registry, request fields, and runtime enforcement while retaining the current default profile behavior.
2. Add ledger JSON persistence and make runtime update its own immutable snapshot after successful or recorded failed turns.
3. Add benchmark cases, fixture executor, CLI, tests, and documentation.
4. Run focused tests, full available Edgmes checks, benchmark self-test, and OpenSpec strict validation.
5. Roll back by selecting the legacy `edge-small` profile and omitting the ledger path; no persisted data migration is required because the new persistence file is opt-in.

## Open Questions

None that change the chosen scope or implementation ordering.
