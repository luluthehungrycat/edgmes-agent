## Purpose

Protects the installable Edgmes namespace from accidental coupling to broad Hermes runtime packages and ensures the edge console entry point is packaged.

## ADDED Requirements

### Requirement: Edgmes package is installable

The project MUST include `edgmes` and `edgmes.*` in package discovery and MUST expose an `edgmes` console entry point targeting the bounded runtime.

#### Scenario: package manifest includes Edgmes
- **WHEN** the package metadata is inspected
- **THEN** discovery includes the Edgmes namespace and the console script is present

### Requirement: Edgmes boundary is explicit

The boundary checker MUST reject direct imports from broad upstream runtime namespaces and references to `~/.hermes` inside `edgmes/` source files.

#### Scenario: forbidden upstream import
- **WHEN** an Edgmes source file imports `agent`, `tools`, `gateway`, `plugins`, or another forbidden upstream namespace directly
- **THEN** the checker exits non-zero and identifies the file and import

#### Scenario: Hermes home reference
- **WHEN** an Edgmes source file references `.hermes` or `HERMES_HOME`
- **THEN** the checker exits non-zero
