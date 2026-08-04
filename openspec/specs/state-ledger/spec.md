# state-ledger Specification

## Purpose
Defines structured, bounded state entries that preserve task continuity without requiring constrained models to receive the complete historical transcript.
## Requirements
### Requirement: Ledger entries are structured and immutable

The system SHALL represent ledger entries with a stable category, content, priority, recency marker, and verification status, and SHALL prevent mutation after creation.

#### Scenario: Valid entry is accepted
- **WHEN** a caller creates an entry with a supported category and non-empty content
- **THEN** the ledger SHALL retain its structured metadata without changing it

#### Scenario: Empty or oversized entry is rejected
- **WHEN** an entry has empty content or exceeds the configured entry limit
- **THEN** entry creation SHALL fail before it can enter the ledger

### Requirement: Ledger preserves bounded continuity categories

The ledger SHALL support identity facts, durable user facts, current goal, constraints, evidence, completed actions, failed actions, changed artifacts, verification state, and next action.

#### Scenario: State categories remain distinguishable
- **WHEN** entries from different categories are added
- **THEN** a context projection SHALL preserve their category labels

### Requirement: Raw transcript is not ledger context

The ledger SHALL store structured state only and SHALL NOT require or embed raw transcript history, credentials, tokens, or sensitive tool arguments.

#### Scenario: Transcript-like content is rejected
- **WHEN** a ledger entry attempts to use a raw transcript category or secret-like metadata
- **THEN** the entry SHALL be rejected

