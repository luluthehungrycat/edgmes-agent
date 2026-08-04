# tool-context-policy Specification

## Purpose
Provides a pure, deterministic boundary that converts requested tools, capabilities, context, and action budgets into an allowed or rejected execution policy without invoking models or performing side effects.
## Requirements
### Requirement: Policy resolution is pure

The resolver SHALL accept immutable profile metadata and a request contract, and SHALL return a structured decision without invoking a model, reading or writing files, accessing credentials, or mutating input objects.

#### Scenario: Valid request produces bounded policy
- **WHEN** requested capabilities, tools, context, and action budgets fit within the selected profile
- **THEN** the resolver SHALL return an allowed decision containing only the permitted tools and bounded budgets

#### Scenario: Resolver does not mutate inputs
- **WHEN** a policy is resolved
- **THEN** the original profile, registry, and request objects SHALL remain unchanged

### Requirement: Tool and capability intersection is fail-closed

The resolver SHALL expose only tools that are both requested and permitted by the selected profile, and SHALL reject any required capability or required tool that the profile cannot provide.

#### Scenario: Optional tool is filtered
- **WHEN** a requested optional tool is not permitted by the profile
- **THEN** the decision SHALL omit that tool while preserving the allowed request if all required items remain satisfiable

#### Scenario: Required tool is unavailable
- **WHEN** a required tool is not permitted by the profile
- **THEN** the resolver SHALL return a rejected decision and SHALL expose no executable toolset

#### Scenario: Required capability is unavailable
- **WHEN** a required capability is not supported by the profile
- **THEN** the resolver SHALL return a rejected decision with a deterministic capability reason

### Requirement: Resource budgets are enforced

The resolver SHALL reject requests whose estimated context, output, steps, or tool calls exceed the profile budgets, and SHALL never increase a requested budget beyond the profile maximum.

#### Scenario: Context boundary is accepted
- **WHEN** estimated context is exactly equal to the profile context budget
- **THEN** the request SHALL remain eligible for policy resolution

#### Scenario: Context overflow is rejected
- **WHEN** estimated context exceeds the profile context budget
- **THEN** the resolver SHALL reject the request before execution

### Requirement: Mutation policy is enforced

The resolver SHALL reject mutation requests unless the selected profile explicitly permits mutation and the request includes the required approval state.

#### Scenario: Read-only request is accepted
- **WHEN** a request does not require mutation
- **THEN** the resolver SHALL not require mutation approval

#### Scenario: Unapproved mutation is rejected
- **WHEN** a request requires mutation without explicit approval
- **THEN** the resolver SHALL return a rejected decision and SHALL expose no executable toolset

