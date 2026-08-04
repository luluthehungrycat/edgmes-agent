# specialist-profile-routing Specification

## Purpose
Provides a bounded routing contract that exposes broad Edgmes capabilities through
small specialist profiles without overwhelming constrained local language models.
## Requirements
### Requirement: Profile registry is explicit

The system SHALL maintain a registry of enabled specialist profiles, where each
profile declares a stable identifier, description, capabilities, available tools,
model policy, action limits, mutation policy, and verification requirements.

#### Scenario: Unknown profile is rejected

- **WHEN** a route request names a profile that is not enabled in the registry
- **THEN** the harness SHALL reject the request without executing a tool or model task

#### Scenario: Profile exposes a bounded toolset

- **WHEN** a specialist profile is selected
- **THEN** the model request SHALL contain only the tools permitted by that profile

### Requirement: Routing precedence is deterministic

The system SHALL evaluate routing sources in this order: explicit profile
selection, deterministic classification, local router-model classification, and
configured larger-model escalation.

#### Scenario: Explicit selection bypasses model routing

- **WHEN** the user or caller explicitly selects an enabled profile
- **THEN** the harness SHALL use that profile without invoking a router model

#### Scenario: Deterministic classification resolves a request

- **WHEN** deterministic classification produces one permitted profile above its
  configured confidence threshold
- **THEN** the harness SHALL select that profile without invoking a router model

#### Scenario: Ambiguous request uses the local router

- **WHEN** deterministic classification is inconclusive and the local router is
  available
- **THEN** the harness SHALL provide the router only the compact profile-routing
  contract and SHALL accept only a validated profile selection

#### Scenario: Router uncertainty escalates

- **WHEN** the local router is unavailable, invalid, or below its confidence
  threshold and escalation is configured
- **THEN** the harness SHALL ask the configured larger model for a route decision
  or return an explicit unresolved-routing result

### Requirement: Router output cannot bypass policy

The harness SHALL validate every selected profile against enabled-profile,
capability, approval, credential, mutation, and risk policy before execution.

#### Scenario: Disallowed mutation route is blocked

- **WHEN** a router selects a profile whose requested action requires mutation that
  is not approved for the current session
- **THEN** the harness SHALL block execution and return a structured policy error

#### Scenario: High-risk profile requires explicit enablement

- **WHEN** a router selects a high-risk profile such as trading, purchasing, or
  computer control without explicit enablement
- **THEN** the harness SHALL reject the route without exposing its tools

### Requirement: Specialist handoff is bounded

The system SHALL pass the selected specialist the original user request plus only
relevant bounded state, routing metadata, constraints, and the selected profile's
tool schemas.

#### Scenario: Raw unrelated transcript is not forwarded

- **WHEN** a route is accepted
- **THEN** the specialist context SHALL omit unrelated historical transcript content
  while preserving the original request and required state

#### Scenario: Specialist returns a structured result

- **WHEN** the specialist finishes or fails
- **THEN** the harness SHALL capture a user-facing result, state updates, changed
  artifacts, verification status, and structured failure information

### Requirement: Routing is observable

The system SHALL record the routing source, candidate profiles, selected profile,
confidence, escalation, policy decision, latency, and outcome without recording
secrets.

#### Scenario: Routing event is auditable

- **WHEN** a route is attempted
- **THEN** an audit event SHALL be emitted with redacted routing metadata and no
  credentials, tokens, or sensitive tool arguments

