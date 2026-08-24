## Context

The proposal describes the motivation. The current downstream `main` contains Edgmes-specific CI classification merged with the runtime/ledger work, while `upstream/main` contains a newer classifier with additional Docker, Nix, lockfile, installer, and Rust lanes. The first real synchronization after the merge conflicts in the classifier and its test file.

## Goals / Non-Goals

**Goals:**

- Produce a reviewable merge of the current upstream classifier into downstream `main`.
- Preserve the union of downstream Edgmes behavior and upstream lane coverage.
- Keep classification conservative for workflow and empty-path changes.
- Make the sync branch pass boundary checks, classifier tests, Edgmes tests, lint, compilation, and the canonical available validation gates.

**Non-Goals:**

- Redesigning the CI workflows themselves.
- Changing the semantics of unrelated upstream product code.
- Automatically resolving future arbitrary upstream conflicts.
- Publishing or merging the synchronization branch without normal review.

## Decisions

### Resolve the classifier semantically, not with ours/theirs

The conflict will be resolved by constructing one classifier that retains both lane vocabularies and their related path predicates. Blindly choosing one side would silently drop either Edgmes protection or upstream validation coverage.

### Keep the downstream fallback behavior explicit

The merged classifier will preserve the downstream Edgmes lane on broad `.github/` and empty-path fallback, while adding upstream broad lanes. This is safer than relying on a future caller to infer that a workflow change affects Edgmes.

### Merge tests by behavior

The test conflict will be resolved into a behavior matrix covering each lane family and combined path sets. Assertions will check lane truth values rather than dictionary ordering or incidental lane counts.

### Validate in a disposable synchronization branch

The implementation branch starts at the exact merged downstream `main`, fetches `upstream/main`, and creates a no-direct-merge review branch. The merge remains reviewable until boundary, focused, full-suite, and static checks pass.

## Risks / Trade-offs

- **[Risk]** Upstream classifier semantics may have hidden interactions not represented by existing tests → **Mitigation:** retain upstream tests, add combined matrix cases, and run the full available suite.
- **[Risk]** A large upstream merge can expose unrelated baseline failures → **Mitigation:** record the exact merge SHA and classify failures by changed path and reproducibility before fixing anything.
- **[Risk]** Broad fallback lanes increase CI cost → **Mitigation:** preserve fail-closed behavior only for empty or `.github/` path sets, matching the safety contract.
- **[Risk]** Upstream may advance during conflict resolution → **Mitigation:** refresh `upstream/main` immediately before final validation and record the exact upstream SHA in the sync PR.

## Migration Plan

1. Implement and test the semantic conflict resolution on this branch.
2. Fetch the current upstream ref and create a dated synchronization branch from downstream `main`.
3. Run boundary, classifier, Edgmes, full available tests, lint, compilation, and diff checks.
4. Push the validated synchronization branch and open a PR targeting downstream `main`.
5. If review identifies a conflict or regression, fix it on the sync branch and rerun the exact-head validation.
6. Rollback is deleting the unmerged synchronization branch; downstream `main` is not changed until the PR is approved and merged.
