## Purpose

Provides a reproducible, versioned way to measure whether Edgmes completes representative tasks safely, efficiently, and verifiably across supported local-model configurations.

## ADDED Requirements

### Requirement: Benchmark covers representative task classes
The benchmark SHALL include inspect, diagnose, single-file edit, test execution, failed-command recovery, and safe multi-step system-task cases with explicit expected outcomes and safety constraints.

#### Scenario: Benchmark suite is enumerated
- **WHEN** the benchmark is invoked
- **THEN** it reports the version and executes every required task class or clearly records an unavailable case

#### Scenario: Destructive action is constrained
- **WHEN** a benchmark case requests a potentially destructive operation
- **THEN** the case requires explicit approval and verifies the postcondition without silently broadening authority

### Requirement: Benchmark reports multidimensional metrics
Each case SHALL report completion, unnecessary or invalid tool calls, context growth, recovery behavior, verification, latency, and destructive-action avoidance metrics in a machine-readable result.

#### Scenario: Case result is recorded
- **WHEN** a benchmark case completes, fails, or times out
- **THEN** its result includes status, metrics, evidence, and a failure reason when applicable

#### Scenario: Results are reproducible
- **WHEN** the same benchmark version, fixture set, and deterministic configuration are run again
- **THEN** the result identifies the same case definitions and records configuration/model metadata needed to compare runs

### Requirement: Benchmark does not mutate the repository implicitly
The benchmark SHALL use isolated fixtures and SHALL report mutations explicitly; a run SHALL NOT modify the project checkout or durable user state unless a case explicitly grants an isolated mutation target.

#### Scenario: Read-only run preserves checkout
- **WHEN** the benchmark runs its inspect or diagnose cases
- **THEN** the repository and durable state remain unchanged

#### Scenario: Isolated edit is verified
- **WHEN** the benchmark runs the edit-and-test case
- **THEN** changes occur only in the case fixture and the expected file/test postconditions are checked
