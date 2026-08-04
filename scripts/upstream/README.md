# Upstream sync scripts

This directory will contain small, auditable helpers for fetching and
classifying upstream changes. The first synchronization workflow should be a
PR-producing operation, not an automatic direct merge into `main`.

Planned checks:

- changed-path classification
- protected Edgmes path detection
- package/import boundary validation
- edge dependency and lockfile verification
- Edgmes smoke tests
