## Purpose

Selects task-relevant context deterministically so model-facing prompts remain within a configured budget while preserving high-priority verified state and the current request.

## ADDED Requirements

### Requirement: Context selection is deterministic and bounded

The selector SHALL accept immutable context items and a positive budget, and SHALL return a stable projection whose serialized size does not exceed that budget.

#### Scenario: Selection fits the budget
- **WHEN** candidate context items fit within the budget
- **THEN** the selector SHALL return them in deterministic priority order

#### Scenario: Selection overflows the budget
- **WHEN** candidates exceed the budget
- **THEN** the selector SHALL omit lower-priority items while retaining mandatory current request context when it fits

### Requirement: Verified and high-priority state wins ties

The selector SHALL rank verified state and higher-priority items ahead of lower-priority or unverified items, with recency and stable identifiers resolving ties.

#### Scenario: Verified evidence displaces stale notes
- **WHEN** both compete for the final budget space
- **THEN** verified evidence SHALL be selected before an otherwise equal stale note

### Requirement: Selection never mutates candidates

The selector SHALL return a projection and SHALL NOT reorder, rewrite, or delete the input ledger or candidate objects.

#### Scenario: Repeated selection is stable
- **WHEN** the same candidates and budget are selected twice
- **THEN** both projections SHALL be identical
