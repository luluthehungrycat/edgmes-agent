## Context

The existing routing layer bounds specialist selection and handoff contents, but model limits are not yet represented as a separate contract. See `proposal.md` for motivation and the capability specs for externally visible behavior.

## Goals / Non-Goals

**Goals:**

- Keep model capability metadata immutable and provider-independent.
- Make tool/context policy resolution deterministic, pure, and independently testable.
- Fail closed for required tools, capabilities, resource overflow, and unapproved mutation.
- Permit optional tools to be filtered without rejecting otherwise valid requests.

**Non-Goals:**

- Selecting a model provider or loading model weights.
- Executing tools, making approvals, or persisting policy decisions.
- Replacing specialist routing or implementing the state ledger.

## Decisions

### Separate model capability profiles from specialist routing

A model capability profile describes what an execution model can safely handle; a specialist profile describes the task role and requested tools. Keeping them separate permits the same specialist to run on multiple model tiers and avoids scattering `edge_mode` branches through routing.

### Use immutable dataclasses and a pure resolver

Frozen value objects make snapshots safe to share and straightforward to test. The resolver receives all inputs explicitly and returns a decision, so tests do not need providers, filesystem state, credentials, or global configuration.

### Fail closed for required items, filter optional items

Required capabilities and tools are part of the task contract and cause rejection when unavailable. Optional tools are removed from the permitted set, preserving useful work while keeping the model's visible tool surface narrow.

### Return bounded budgets rather than trusting requests

The profile remains authoritative. The resolver clamps execution budgets downward to profile limits and rejects only values that make the request unsatisfiable, such as context overflow or a requested step count above the profile maximum.

## Risks / Trade-offs

- [Risk] Static capability metadata can become stale as tools evolve → keep profiles explicit and validate tool identifiers at the policy boundary.
- [Risk] A strict fail-closed policy may reject useful work → distinguish required from optional requirements and expose deterministic reasons for routing or escalation.
- [Risk] Context estimates may be approximate → treat estimates as admission control, not a claim about tokenizer-exact usage; later context-ledger work can provide measured accounting.

## Migration Plan

Add the contracts alongside the existing routing module. Existing routing behavior remains unchanged until a later edge-runtime integration explicitly supplies a capability profile to the resolver. No Hermes state migration is required.
