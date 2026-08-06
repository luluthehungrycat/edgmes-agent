## Context

Edgmes is a downstream distribution with `origin/main` as product history and `upstream/main` as vanilla Hermes. Existing CI covers the inherited tree but does not prove the Edgmes package is included in setuptools or prevent direct imports from broad upstream runtime namespaces.

## Decisions

- keep sync as a branch-and-PR operation;
- classify upstream changes using the upstream-only merge-base diff;
- fail boundary checks on forbidden imports, Hermes-home references, missing package discovery, or missing CLI entry point;
- run focused Edgmes tests and boundary checks in a path-scoped edge workflow.
