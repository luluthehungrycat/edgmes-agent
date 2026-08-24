## Purpose

Ensures contributor attribution remains meaningful for downstream synchronization branches by validating local sync authors while excluding the upstream history intentionally imported by the synchronization merge.

## ADDED Requirements

### Requirement: Imported upstream history is excluded from downstream attribution

The attribution check MUST exclude commits reachable from the second parent of the synchronization merge while continuing to inspect downstream commits introduced before or after that merge.

#### Scenario: Sync branch imports upstream history

- **WHEN** a synchronization branch contains a merge commit that imports upstream history
- **THEN** contributor attribution checks downstream sync commits but does not require mappings for authors whose commits are reachable only from that second parent

#### Scenario: Ordinary feature branch has no sync merge

- **WHEN** a non-synchronization branch contains no canonical upstream synchronization merge
- **THEN** contributor attribution checks all non-merge commits introduced after the downstream merge base using the existing behavior

#### Scenario: Sync branch contains a local commit after the merge

- **WHEN** a downstream contributor adds a commit after the upstream synchronization merge
- **THEN** that contributor email remains included in attribution checking
