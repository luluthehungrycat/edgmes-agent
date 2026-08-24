## 1. Conflict-resolution implementation

- [x] 1.1 Merge current `upstream/main` into an isolated synchronization worktree based on the merged downstream `main` and record the exact upstream and merge-base SHAs.
- [x] 1.2 Resolve `scripts/ci/classify_changes.py` by preserving Edgmes routing and upstream Docker, Nix, lockfile, installer, Rust, frontend, site, scan, dependency, MCP, and review lanes.
- [x] 1.3 Resolve `tests/ci/test_classify_changes.py` into a behavior matrix covering Edgmes paths, upstream-only paths, combined paths, and empty/`.github/` fallback.

## 2. Validation

- [x] 2.1 Run the classifier-focused tests and confirm every combined lane assertion passes.
- [x] 2.2 Run the Edgmes boundary checks, focused Edgmes tests, compilation, and changed-file lint.
- [ ] 2.3 Run the canonical available repository test suite and classify any unrelated or baseline failures without masking them.
- [x] 2.4 Confirm the synchronization worktree is clean, has no conflict markers, and contains only the validated merge result.

## 3. Reviewable publication

- [ ] 3.1 Push the validated synchronization branch from the exact merged downstream base.
- [ ] 3.2 Open or update the upstream synchronization PR with the upstream SHA, merge base, risk classification, conflict-resolution summary, and validation evidence.
- [ ] 3.3 Run fresh exact-head review and required CI; do not merge until blockers are resolved and all required checks pass.
