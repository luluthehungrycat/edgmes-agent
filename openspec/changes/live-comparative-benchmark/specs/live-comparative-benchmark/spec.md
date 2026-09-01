## Purpose

Provides honest, comparable machine-readable evidence about model behavior at the context budgets used by the Edgmes roadmap.

## ADDED Requirements

### Requirement: The benchmark SHALL cover the standard context budgets
A benchmark invocation SHALL produce one result for every selected task and each requested 16K, 32K, 48K, or 64K token budget, with all four budgets selected by default.

#### Scenario: Default comparative sweep
- **WHEN** the benchmark runs with default options
- **THEN** its machine-readable output contains six task results at each of 16K, 32K, 48K, and 64K tokens

### Requirement: Results SHALL expose multidimensional live metrics
Each request result SHALL include status, completion, verification, tool-call count, latency, prompt/response size, requested context budget, and an explicit failure reason when it did not pass.

#### Scenario: Backend returns a valid plan
- **WHEN** a provider-neutral backend returns valid JSON
- **THEN** the result records a passed completion and its measured latency and tool-call metric

### Requirement: Unavailable backends SHALL fail honestly
When credentials are absent or the configured backend cannot be reached, the benchmark SHALL emit unavailable results with no fabricated plan or success metric and SHALL distinguish them from malformed model output failures.

#### Scenario: Offline invocation
- **WHEN** no API key is configured
- **THEN** every requested result is unavailable, completion and verification are false, and the summary reports the unavailable count

### Requirement: Credentials SHALL remain out of artifacts
The benchmark SHALL read credentials only from the configured environment variable and SHALL NOT include the credential in output or exception reporting.

#### Scenario: Machine-readable output is saved
- **WHEN** a run writes a JSON report
- **THEN** the report contains model and endpoint mode metadata but no API key value
