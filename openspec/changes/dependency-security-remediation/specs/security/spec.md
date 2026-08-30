## ADDED Requirements

### Requirement: Patched fixed-version dependencies
The remediation branch MUST update every dependency with a published safe version
that is directly controlled by the repository and compatible with the existing
package constraints.

#### Scenario: OSV-fixed dependencies are resolved
- **WHEN** the tracked lockfiles are scanned
- **THEN** Electron, NanoID, and h2 resolve to versions containing their
  published fixes

### Requirement: No silent security suppression
The remediation MUST NOT suppress an OSV finding without recording the package,
reachability, reason, and follow-up disposition.

#### Scenario: A dependency has no upstream patch
- **WHEN** an affected package has no patched release
- **THEN** the security documentation records the limitation and follow-up
  disposition

### Requirement: Reproducible validation
The remediation MUST leave package lockfiles internally consistent and pass
OSV scanning plus the affected workspace checks.

#### Scenario: Clean supported-toolchain install
- **WHEN** CI performs a locked dependency installation
- **THEN** the installation succeeds without modifying the lockfiles
