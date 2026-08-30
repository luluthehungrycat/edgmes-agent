## 1. Conflict-resolution implementation

- [x] 1.1 Merge current `upstream/main` into an isolated synchronization worktree based on the merged downstream `main` and record the exact upstream and merge-base SHAs.
- [x] 1.2 Resolve `scripts/ci/classify_changes.py` by preserving Edgmes routing and upstream Docker, Nix, lockfile, installer, Rust, frontend, site, scan, dependency, MCP, and review lanes.
- [x] 1.3 Resolve `tests/ci/test_classify_changes.py` into a behavior matrix covering Edgmes paths, upstream-only paths, combined paths, and empty/`.github/` fallback.
- [x] 1.4 Update the contributor attribution boundary so imported upstream history is excluded while downstream sync commits remain checked.
- [x] 1.5 Make large synchronization branches bypass compare-API narrowing and fail open to all validation lanes.

## 2. Validation

- [x] 2.1 Run the classifier-focused tests and confirm every combined lane assertion passes.
- [x] 2.2 Run the Edgmes boundary checks, focused Edgmes tests, compilation, and changed-file lint.
- [ ] 2.3 Run the canonical available repository test suite and classify any unrelated or baseline failures without masking them.

> Current evidence for 2.3: collection completes with 38,491 selected tests, but the full run does not complete reliably on this VPS. The first isolated failure is the upstream `tests/agent/test_auxiliary_explicit_cancellation.py::test_cancelled_codex_orphan_timeout_preserves_cached_shared_client`, which failed twice and passed once in three serial reruns. A later E2E path also emitted repeated temporary-log-directory `FileNotFoundError` failures. Neither path is touched by this conflict-resolution change.
- [x] 2.4 Confirm the synchronization worktree is clean, has no conflict markers, and contains only the validated merge result.
- [x] 2.5 Add regression coverage for ordinary branches, sync branches, and downstream commits after an upstream merge.
- [x] 2.6 Validate synchronization branch detection and all-lane fail-open behavior in the composite action path.
- [x] 2.7 Restore bounded Python test slicing and JS/TS workspace fan-out after the upstream monolithic runner assumptions caused timeout-sensitive failures on standard hosted runners.

## 3. Reviewable publication

- [x] 3.1 Push the validated synchronization branch from the exact merged downstream base.
- [x] 3.2 Open or update the upstream synchronization PR with the upstream SHA, merge base, risk classification, conflict-resolution summary, and validation evidence.
- [ ] 3.3 Run fresh exact-head review and required CI; do not merge until blockers are resolved and all required checks pass.
