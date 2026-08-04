## Purpose

Executes bounded Edgmes turns against an injected local chat backend while enforcing model capability limits, compact context selection, immutable state updates, and explicit verification metadata.

## ADDED Requirements

### Requirement: Runtime resolves policy before backend access

The runtime SHALL resolve the selected model capability profile and SHALL reject a request before calling the backend when its context, output, step, or tool requirements exceed policy.

#### Scenario: Allowed request reaches backend
- **WHEN** a request fits the selected profile
- **THEN** the runtime SHALL call the backend with only the bounded policy-approved request context

#### Scenario: Disallowed request is rejected
- **WHEN** a request exceeds profile limits
- **THEN** the runtime SHALL return a structured rejection without calling the backend

### Requirement: Runtime uses bounded ledger context

The runtime SHALL select ledger entries under the profile context budget and SHALL include the current request as mandatory model-facing context.

#### Scenario: Context is projected before generation
- **WHEN** a turn has prior ledger state
- **THEN** the backend SHALL receive the deterministic bounded projection rather than the raw transcript

### Requirement: Runtime records verifiable results

The runtime SHALL return response text, profile metadata, selected context identifiers, and backend evidence, and SHALL append response and verification state to a new ledger snapshot.

#### Scenario: Successful local turn
- **WHEN** the backend returns a valid response
- **THEN** the runtime SHALL expose the response and a ledger snapshot containing the completed action and verification state

### Requirement: Ollama transport is bounded and explicit

The Ollama backend SHALL use an explicit base URL, model, non-streaming chat request, timeout, and response validation; it SHALL not read Hermes credentials or global Hermes state.

#### Scenario: Local endpoint responds
- **WHEN** the configured Ollama endpoint returns valid chat JSON
- **THEN** the backend SHALL return normalized response text and usage/evidence metadata
