## Why

Edgmes currently routes requests to bounded specialist profiles, but it does not yet express the limits of the model executing a profile. Small local models need deterministic limits on context size, tool exposure, action count, and mutation before any model request is assembled. A pure policy layer makes those limits testable and keeps execution authority outside the model.

## What Changes

- Add immutable model capability profiles for constrained local models.
- Add a pure resolver that intersects requested tools and capabilities with the selected model profile and session policy.
- Reject requests that exceed context, action, mutation, or capability limits without constructing an executable handoff.
- Return deterministic decisions containing the permitted tools, budgets, and rejection reasons.
- Document the contract and provide focused tests for accepted, rejected, and boundary requests.

## Capabilities

### New Capabilities

- `model-capability-profiles`: Describe bounded model capabilities, budgets, and tool exposure.
- `tool-context-policy`: Resolve a bounded execution policy without model, filesystem, or provider side effects.

### Modified Capabilities

- None.

## Impact

- New public contracts under `edgmes/`.
- New Edgmes tests and documentation.
- No changes to inherited Hermes runtime modules, provider APIs, credentials, or global Hermes state.
