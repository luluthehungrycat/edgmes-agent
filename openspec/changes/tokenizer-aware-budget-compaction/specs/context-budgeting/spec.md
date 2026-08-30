## Purpose

Bounds the exact rendered context sent to an Edgmes backend using an injected tokenizer when available and a conservative deterministic fallback otherwise.

## ADDED Requirements

### Requirement: Context measurement is explicit

The system SHALL report the measurement mode, measured value, and active budget for every bounded projection.

#### Scenario: Tokenizer is available
- **WHEN** a valid tokenizer adapter measures the rendered backend context
- **THEN** the projection SHALL use that token count and identify tokenizer measurement mode

#### Scenario: Tokenizer is unavailable or fails
- **WHEN** no adapter exists or it returns an invalid count
- **THEN** the projection SHALL use the documented conservative fallback and identify fallback mode without exceeding the configured budget

### Requirement: Backend context never exceeds budget

The system SHALL measure the exact rendered text sent to the backend, including system instructions and separators, and SHALL reject a projection that exceeds the active budget.

#### Scenario: Artificial edge budgets
- **WHEN** the active budget is 16K, 32K, 48K, or 64K
- **THEN** the rendered backend context SHALL remain within that budget or fail closed with a structured reason
