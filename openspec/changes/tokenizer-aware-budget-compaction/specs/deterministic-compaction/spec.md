## Purpose

Compacts model-facing Edgmes context reproducibly while preserving mandatory and verified state.

## ADDED Requirements

### Requirement: Compaction is deterministic and immutable

The system SHALL produce the same selected IDs, rendered text, and omission metadata for identical inputs and SHALL NOT mutate source entries or ledgers.

#### Scenario: Repeated compaction
- **WHEN** the same ledger and budget are compacted twice
- **THEN** both results SHALL be identical, including ordering and omission reasons

### Requirement: Mandatory state is preserved

The system SHALL retain the current request and every other mandatory entry when they fit within the measured budget, and SHALL fail closed when they do not.

#### Scenario: Lower-value history competes for space
- **WHEN** mandatory or verified entries compete with stale/unverified entries
- **THEN** mandatory and verified entries SHALL be selected first and omitted history SHALL be reported
