## Context

Capability profiles and ledger selection are now available as pure seams. The runtime must compose them without importing the inherited 7,000-line conversation loop or broad tool registry. The live acceptance path uses the already-running Ollama HTTP service.

## Goals / Non-Goals

**Goals:**

- Provide a small, testable runtime state machine for one bounded turn.
- Enforce policy and context limits before network access.
- Keep backend transport injectable and dependency-free.
- Make a real local Ollama task reproducible from the command line.

**Non-Goals:**

- Reimplementing Hermes provider failover, streaming, approvals, or all tools.
- Persisting Edgmes state to disk in this milestone.
- Adding automatic model downloads.
- Treating model text as authorization to mutate the host.

## Decisions

### Inject a backend protocol

The runtime depends on a minimal `complete(messages, model, max_output)` protocol. Tests can use a deterministic fake; Ollama is one concrete adapter. This avoids importing `openai` or coupling the core to one provider SDK.

### Use one-shot bounded turns first

A one-shot turn provides a verifiable runtime seam and local-model acceptance test without recreating an unrestricted ReAct loop. Tool execution and multi-step state transitions can be added behind the existing policy limits later.

### Use ledger projection, not transcript replay

The runtime creates a mandatory current-request entry, selects bounded prior state, and sends only a compact system/request projection. The raw Hermes transcript remains outside this runtime.

### Treat backend output as untrusted evidence

Response text is recorded as completed output and verification metadata, but it cannot authorize tools or mutations. The runtime exposes no executable tools in this milestone.

## Risks / Trade-offs

- [Risk] Ollama response formats vary → validate required fields and return structured transport errors.
- [Risk] Character budget approximates tokens → reserve output separately and use the profile's conservative context budget.
- [Risk] One-shot runtime is not full agent parity → keep the seam explicit and make later tool loops bounded by the same resolver.

## Migration Plan

Add the runtime alongside existing Hermes entry points. Invoke it explicitly with `python -m edgmes.runtime`; no existing command or state path changes.
