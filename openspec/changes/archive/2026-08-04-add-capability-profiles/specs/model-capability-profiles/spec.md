## Purpose

Defines explicit, immutable model limits so Edgmes can select safe execution budgets for local models with constrained context windows and tool-calling abilities.

## ADDED Requirements

### Requirement: Capability profiles are explicit

The system SHALL represent each enabled model capability profile with a stable identifier, context budget, output budget, supported capabilities, permitted tools, action limits, tool-calling support, and mutation policy.

#### Scenario: Profile exposes bounded metadata
- **WHEN** a capability profile is catalogued
- **THEN** its catalog entry SHALL contain only deterministic non-secret metadata needed for policy resolution

#### Scenario: Invalid profile limits are rejected
- **WHEN** a profile declares a non-positive context, output, step, or tool-call budget
- **THEN** profile construction SHALL fail before the profile can be enabled

### Requirement: Profile registries are immutable during resolution

The system SHALL resolve a request against a snapshot of enabled capability profiles and SHALL NOT mutate the registry or profile objects while resolving it.

#### Scenario: Concurrent callers receive stable policy inputs
- **WHEN** two requests resolve against the same registry snapshot
- **THEN** each request SHALL observe the same profile metadata unless a new registry snapshot is explicitly supplied

### Requirement: Profiles do not contain secrets

Capability profile metadata SHALL NOT store credentials, tokens, passwords, connection strings, or provider secrets.

#### Scenario: Secret-like metadata is rejected
- **WHEN** a profile includes secret-like keys or values in extensible metadata
- **THEN** profile construction SHALL reject the profile rather than persist or expose the value
