## Purpose

Carries verified, secret-safe continuity between bounded runtime turns while guaranteeing deterministic context selection, omission reporting, and durable recovery across fresh processes.

## ADDED Requirements

### Requirement: Runtime turns produce bounded ledger state
Each completed runtime turn SHALL record the current request, completion outcome, and verification result in immutable ledger state. Ledger entries SHALL reject secret-like content and duplicate identifiers.

#### Scenario: Successful turn records continuity
- **WHEN** a backend returns a non-empty response for a valid bounded request
- **THEN** the runtime result contains immutable ledger state with the request, completion, and verification entries

#### Scenario: Secret-like state is rejected
- **WHEN** a caller attempts to add ledger content or metadata containing credential-like markers
- **THEN** the ledger rejects the entry and does not expose it to runtime context

### Requirement: Context projection stays within the active budget
The runtime SHALL select whole ledger entries deterministically within the active profile context budget, always include the current request, and report omitted non-mandatory entries.

#### Scenario: Older low-priority state is omitted
- **WHEN** accumulated ledger entries exceed the active context budget
- **THEN** the runtime includes mandatory/current and higher-ranked entries within budget and reports omitted entry identifiers

#### Scenario: Mandatory request cannot fit
- **WHEN** the current request and runtime instructions cannot fit within the active context budget
- **THEN** the runtime rejects the request with a bounded-context error before backend invocation

### Requirement: Ledger state survives a fresh process
The runtime SHALL provide a documented persistence representation that can be saved and loaded without changing entry identity, ordering semantics, verification state, or secret-safety checks.

#### Scenario: Persisted ledger reloads
- **WHEN** a ledger is saved and loaded in a fresh process
- **THEN** the reloaded ledger produces the same deterministic context projection for the same budget

#### Scenario: Invalid persisted data is rejected
- **WHEN** persisted ledger data is malformed, duplicated, or contains secret-like content
- **THEN** loading fails closed without constructing a usable unsafe ledger
