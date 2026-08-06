## Why

The downstream now has enough edge-specific behavior to require automated protection against accidental upstream coupling and an auditable synchronization path. Packaging must expose `edgmes` without importing broad Hermes integrations.

## Scope

Add a reviewable upstream-sync helper, an Edgmes package-boundary checker, a console entry point, and focused edge CI. The workflow may open a PR but must never merge directly into downstream `main`.
