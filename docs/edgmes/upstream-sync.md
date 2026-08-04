# Upstream synchronization policy

## Remotes

```text
origin    git@github.com:luluthehungrycat/edgmes-agent.git
upstream  https://github.com/NousResearch/hermes-agent.git
```

`origin` is the Edgmes product repository. `upstream` is read-only from the
perspective of routine downstream work.

## Branches

- `main`: Edgmes development branch
- `sync/upstream-YYYY-MM-DD`: temporary upstream synchronization branches
- `feature/*`: focused Edgmes changes

## Synchronization workflow

```bash
git fetch upstream
git switch -c sync/upstream-$(date +%F)
git merge --no-ff upstream/main
```

Run the Edgmes smoke tests, package-boundary checks, and relevant upstream
tests before opening a pull request into `main`.

## Review policy

Changes that only affect documentation, tests, or code excluded from the
Edgmes runtime may be eligible for automated merging after CI.

Human review is required for changes touching:

- the agent loop
- context selection or compression
- prompt construction
- tool discovery or dispatch
- session and memory persistence
- approvals and security boundaries
- package manifests and dependency groups

Never apply only part of an upstream commit merely because one changed path
looks relevant. Classify by path, but merge or review the complete logical
change together with its tests and configuration.
