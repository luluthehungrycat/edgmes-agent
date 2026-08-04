# edgmes-home-isolation Specification

## Purpose
Provides an independent Edgmes state root so Edgmes can be installed and used
alongside standard Hermes Agent without silently sharing configuration or state.
## Requirements
### Requirement: Edgmes has an independent default home

The system SHALL resolve the default Edgmes home to `~/.edgmes` for configuration,
sessions, persistent state, skills, cache, logs, and runtime metadata.

#### Scenario: Default home is independent from Hermes

- **WHEN** no explicit Edgmes home is configured
- **THEN** the system SHALL use `~/.edgmes` and SHALL NOT write Edgmes state under
  `~/.hermes`

#### Scenario: Existing Hermes home is preserved

- **WHEN** `~/.hermes` exists before Edgmes starts
- **THEN** Edgmes SHALL leave its contents unchanged unless the user explicitly
  configures an import or migration

### Requirement: Home override is explicit

The system SHALL support an explicit environment or command-line override for the
Edgmes home and SHALL resolve it deterministically before loading state.

#### Scenario: Environment override is honored

- **WHEN** the supported Edgmes home environment variable is set to an absolute path
- **THEN** the system SHALL use that path as its home root

#### Scenario: Relative home override is rejected

- **WHEN** an Edgmes home override is relative or otherwise invalid
- **THEN** the system SHALL fail with a clear configuration error before writing state

### Requirement: Home directories have defined boundaries

The system SHALL keep Edgmes configuration, state, sessions, skills, cache, logs,
and runtime metadata in named subdirectories below the resolved Edgmes home.

#### Scenario: Runtime directories are discoverable

- **WHEN** the Edgmes home is initialized
- **THEN** the system SHALL expose deterministic paths for each supported state
  category without creating unrelated Hermes directories

### Requirement: No implicit cross-home reads or writes

The system SHALL NOT read credentials, profiles, memories, sessions, or skills from
`~/.hermes` merely because that directory exists.

#### Scenario: Hermes data is not implicitly loaded

- **WHEN** both `~/.edgmes` and `~/.hermes` exist
- **THEN** Edgmes SHALL load only configured Edgmes sources and SHALL report missing
  Edgmes state rather than silently falling back to Hermes state

#### Scenario: Explicit migration is distinguishable

- **WHEN** the user requests an import or migration from Hermes
- **THEN** the operation SHALL be explicit, reviewable, and separate from normal
  Edgmes startup

