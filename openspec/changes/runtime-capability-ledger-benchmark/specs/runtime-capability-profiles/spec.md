## Purpose

Provides explicit, named execution contracts so edge models receive only the capabilities, tools, context, and mutation authority appropriate to their declared tier.

## ADDED Requirements

### Requirement: Named profiles constrain runtime requests
The runtime SHALL support named capability profiles with explicit context, output, step, tool-call, capability, and permitted-tool limits. An unknown profile SHALL fail closed before a backend request is made.

#### Scenario: Allowed request uses the selected profile
- **WHEN** a request selects a known profile and fits its required capabilities, tools, and budgets
- **THEN** the runtime sends a backend request using only the profile-permitted tools and limits

#### Scenario: Unknown profile is rejected
- **WHEN** a request names a profile that is not present in the configured profile catalog
- **THEN** the runtime rejects the request without invoking the backend

### Requirement: Tool exposure is filtered before request construction
The runtime SHALL exclude optional tools not permitted by the selected profile and SHALL reject requests whose required tools or capabilities are unavailable.

#### Scenario: Optional tools are filtered
- **WHEN** a request includes both permitted and non-permitted optional tools
- **THEN** the backend request contains only the permitted optional tools and the result records the filtered tools

#### Scenario: Required capability is unavailable
- **WHEN** a request requires a capability absent from the selected profile
- **THEN** the runtime rejects the request and identifies the missing capability

### Requirement: Budgets and mutation approval are enforced
The runtime SHALL reject requests exceeding profile context, output, step, or tool-call limits. A mutation request SHALL require both profile mutation authority and explicit request approval.

#### Scenario: Budget overflow is rejected
- **WHEN** estimated context, requested output, steps, or tool calls exceeds the selected profile limit
- **THEN** the runtime rejects the request before backend invocation

#### Scenario: Mutation lacks approval
- **WHEN** a request requires mutation but the profile disallows mutation or the request lacks explicit approval
- **THEN** the runtime rejects the request before any mutation-capable operation is exposed
