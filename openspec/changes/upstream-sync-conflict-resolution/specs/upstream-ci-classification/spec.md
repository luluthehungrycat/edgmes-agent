## Purpose

Preserves the downstream and upstream CI routing contracts when a high-risk upstream synchronization changes the shared path classifier.

## ADDED Requirements

### Requirement: Combined lane classification is preserved

The synchronization result MUST retain all downstream Edgmes lane decisions and all upstream lane decisions for Docker, Nix, lockfile, installer, Rust, frontend, site, scan, dependency, MCP, and review checks.

#### Scenario: Edgmes source changes remain Edgmes-scoped

- **WHEN** a synchronized change contains only Edgmes source, Edgmes tests, Edgmes scripts, or Edgmes documentation paths
- **THEN** the classifier marks the Edgmes lane for execution and does not remove unrelated upstream lane keys from its result

#### Scenario: Upstream Rust changes select the Rust lane

- **WHEN** a synchronized change contains a Rust source file or Rust crate manifest
- **THEN** the classifier marks the Rust lane and returns a complete lane mapping

#### Scenario: Upstream Nix changes select the Nix lane

- **WHEN** a synchronized change contains a Nix path or flake file
- **THEN** the classifier marks the Nix lane and does not incorrectly require Python lanes solely because the file is Nix-specific

### Requirement: Broad CI changes fail closed to broad validation

The classifier MUST mark the broad safety lanes when the changed path set is empty or contains `.github/` workflow or action files, including the combined upstream and downstream lane keys.

#### Scenario: Workflow change triggers broad validation

- **WHEN** a synchronized change contains a `.github/` workflow or action path
- **THEN** Python, Docker, frontend, site, scan, dependency, lockfile, installer, Rust, Nix, and CI-review lanes are marked for execution, and the Edgmes lane remains enabled

#### Scenario: Empty change set is classified conservatively

- **WHEN** the classifier receives an empty path list
- **THEN** it returns the same broad fail-closed lane selection as a workflow change

### Requirement: Classifier behavior is regression-tested

The synchronization change MUST include executable tests covering downstream Edgmes paths, upstream-only lane paths, combined path sets, and broad fallback behavior.

#### Scenario: Combined path matrix remains stable

- **WHEN** the test suite classifies a representative set containing Edgmes, Docker, Nix, lockfile, installer, Rust, and frontend paths
- **THEN** every expected lane is asserted and the test passes without relying on dictionary ordering
