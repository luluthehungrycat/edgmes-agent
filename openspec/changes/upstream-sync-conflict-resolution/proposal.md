## Why

The first post-merge upstream synchronization attempt exposed a real merge conflict in the shared CI change classifier and its tests. The downstream sync process must preserve Edgmes-specific lane classification while incorporating upstream CI lanes, and it must produce a reviewable, validated synchronization branch instead of leaving this conflict to an opaque scheduled failure.

## What Changes

- Resolve the upstream merge conflict in `scripts/ci/classify_changes.py` without dropping either downstream Edgmes routing or upstream Docker, Nix, lockfile, installer, and Rust lanes.
- Merge the corresponding classifier regression tests and add coverage for the combined lane contract.
- Make the synchronization branch reproducible from the merged downstream `main` and validate its boundary, focused tests, lint, and complete available suite before publication.
- Record the resolved synchronization and its remaining high-risk review boundary in OpenSpec artifacts.

## Capabilities

### New Capabilities

- `upstream-ci-classification`: Preserve and validate the combined downstream/upstream CI lane classification contract during synchronization.
- `upstream-contributor-attribution`: Check downstream-authored sync commits without treating imported upstream history as new downstream contributions.

### Modified Capabilities

- None.

## Impact

Affected areas include `scripts/ci/classify_changes.py`, `tests/ci/test_classify_changes.py`, upstream synchronization branches and workflow validation, and CI lane selection. No public runtime API or package dependency is intended to change.
