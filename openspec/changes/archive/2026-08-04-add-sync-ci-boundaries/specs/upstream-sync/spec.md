## Purpose

Makes upstream synchronization reviewable and classifies risk before a merge is attempted.

## ADDED Requirements

### Requirement: upstream changes are classified from the merge-base diff

The sync helper MUST compare the merge base of downstream `main` and `upstream/main` with `upstream/main`, not compare downstream-only files as upstream changes.

#### Scenario: upstream is ahead
- **WHEN** upstream contains commits after the common ancestor
- **THEN** the helper reports changed paths, commit count, and protected-path risk labels

### Requirement: synchronization requires a topic branch and PR

The automation MUST create a `sync/upstream-YYYY-MM-DD` branch and MUST NOT merge directly into downstream `main`.

#### Scenario: scheduled sync
- **WHEN** a scheduled sync finds upstream changes
- **THEN** it pushes the sync branch and opens or updates a PR targeting `main`

#### Scenario: merge conflict
- **WHEN** the upstream merge conflicts
- **THEN** the workflow fails without pushing a partially merged branch or changing `main`
