## Why

Small local models should not be forced to reason over every Edgmes tool and
integration at once. Edgmes needs a narrow, deterministic capability boundary
per invocation while still making a broad set of specialist workflows
available. An efficient local router should handle ambiguous requests before
escalating to a larger model, and Edgmes must not collide with a standard
Hermes installation's state and configuration directories.

## What Changes

- Add a declarative specialist profile registry with narrow tool and capability
  bundles.
- Add routing precedence: explicit selection, deterministic classification,
  local FunctionGemma routing for ambiguity, then configured larger-model
  escalation.
- Add a single compact routing contract rather than exposing every specialist
  as a full tool schema.
- Validate routed profiles in the harness; model-selected routes cannot bypass
  profile, approval, credential, or mutation policy.
- Define a bounded context handoff from the router to the selected specialist.
- Establish `~/.edgmes` as the default Edgmes home for configuration, state,
  sessions, cache, skills, and logs, independent of `~/.hermes`.
- Add tests for routing, fallback, policy enforcement, context handoff, and
  home-directory isolation.

## Capabilities

### New Capabilities

- `specialist-profile-routing`: Route requests to a bounded specialist profile
  using explicit, deterministic, local-model, and escalation paths.
- `edgmes-home-isolation`: Resolve Edgmes global state and configuration under
  `~/.edgmes` without implicitly reading or writing standard Hermes state.

### Modified Capabilities

- None.

## Impact

- New Edgmes modules under `edgmes/` for profile metadata, routing policy,
  context handoff, and home-directory resolution.
- New profile and routing configuration under the Edgmes home.
- New tests under `tests/edgmes/`.
- Future CLI and runtime integration points, without changing the inherited
  Hermes conversation loop in this change.
- FunctionGemma is an optional local routing model; the design must work with
  deterministic routing alone when it is unavailable.
- No user credentials or standard Hermes profile data are migrated or copied
  implicitly.
