# Upstream sync and edge CI

Edgmes keeps the downstream product on `origin/main` and vanilla Hermes on the
read-only `upstream` remote.

## Inspect the upstream delta

From a clean checkout with both remotes fetched:

```bash
python3 scripts/upstream/sync.py --json
```

The helper computes the merge base of `origin/main` and `upstream/main`, then
classifies only upstream-side changes. It reports the commit count, changed
paths, protected runtime/prompt/tool/state paths, and a `normal` or `high` risk
label. It does not mutate the checkout by default.

## Create a sync branch manually

```bash
git fetch upstream main
python3 scripts/upstream/sync.py \
  --create-branch \
  --branch "sync/upstream-$(date -u +%F)"
```

The command requires a clean working tree and uses `git merge --no-ff`. A
conflict stops the operation; resolve and verify it manually before pushing.
Never merge directly into `main`. Open a PR from the
`sync/upstream-YYYY-MM-DD-run-N` branch and review high-risk paths explicitly.

## Automation

`.github/workflows/edgmes-upstream-sync.yml` runs weekly and on manual dispatch.
It fetches the official upstream, classifies the delta, creates a run-unique
sync branch, runs Edgmes boundary/focused tests without a write token, then
publishes the already-validated commit and opens a PR. It has no direct `main`
merge step.

`.github/workflows/edgmes-edge.yml` runs on Edgmes/package changes and checks:

- package discovery and the installed `edgmes` console script;
- forbidden upstream imports and Hermes-home references;
- focused Edgmes tests;
- compilation and Ruff.

## Protected review areas

Changes touching the inherited conversation loop, prompt/context selection,
tool discovery/dispatch, session/memory persistence, approvals, security
boundaries, or package manifests require human review even when automated edge
checks pass.
