# Edgmes Agent implementation roadmap

> **Product name:** Hermes Agent Edge
>
> **Technical name:** Edgmes Agent
>
> **Repository:** `edgmes-agent`

## Goal

Build an edge-oriented Hermes runtime for local 1–7B models and 16k–64k
context windows while preserving useful Hermes identity, profiles, skills,
memory, sessions, approvals, and persistence.

## Guiding constraints

- Keep the inherited Hermes tree intact while boundaries are established.
- Put Edgmes-specific policy under `edgmes/`.
- Prefer pure, testable policy objects before changing the conversation loop.
- Construct only the tools and context needed for the current task.
- Keep mutations explicit and require postcondition verification.
- Treat upstream synchronization as a reviewable, tested operation.
- Do not infer capability from parameter count alone; record observed behavior.

## Milestones

### 0. Baseline and contract

**Status:** baseline harness complete; runtime contract work continues.

The reproducible harness is `scripts/benchmarks/baseline_harness.py` and its
usage is documented in `docs/edgmes/baseline-harness.md`. It measures the
inherited runtime without provider calls or repository mutation:

- process/import startup time
- tool discovery and construction time
- system-prompt assembly time and character size
- one representative read-only task

A three-iteration run on the development host recorded these medians:

```text
run_agent import:             1102 ms
prompt assembly subprocess:    222 ms / 18,827 chars
built-in tool construction:    725 ms / 36 modules / 81 tools
read-only task subprocess:      42 ms
```

These are preparation baselines, not model-quality or first-token benchmarks.
Provider/model initialization, first-token latency, tool-call latency, and
context-compression behavior remain later benchmark work. The baseline must run
without modifying upstream runtime behavior.

### 1. Capability profiles

**Status:** model capability contracts and pure tool/context resolver complete;
profile presets and runtime integration remain.

Implemented under `edgmes/capabilities.py`:

- immutable context and input/output budgets;
- supported capabilities and permitted tools;
- maximum steps and tool calls;
- explicit mutation approval policy;
- fail-closed required-tool/capability handling;
- optional-tool filtering;
- deterministic structured policy decisions.

The resolver is intentionally not wired into the inherited conversation loop yet.
Initial named presets (`nano`, `small`, `medium-edge`, `full`), retry/delegation/
parallelism policy, compression policy, and observed model metadata remain part of
runtime integration work.

### 2. Bounded context and state ledger

**Status:** structured ledger and deterministic bounded selector complete;
edge-runtime integration remains.

Implemented under `edgmes/ledger.py`:

- immutable continuity entries for goals, constraints, evidence, actions,
  artifacts, verification, and next actions;
- transcript/secret rejection at the ledger boundary;
- immutable ledger snapshots;
- deterministic priority/verification/recency ranking;
- whole-entry greedy packing under a character budget;
- mandatory current-request handling and omission reporting.

Raw Hermes transcript persistence remains untouched. Tokenizer-aware budgeting,
deterministic compaction, and runtime integration remain next-stage work.

### 3. Edge tool policy and runtime

**Status:** bounded one-shot runtime and real local-model smoke complete.

Implemented under `edgmes/runtime.py`:

- provider-neutral injected `ChatBackend` protocol;
- dependency-free non-streaming Ollama adapter;
- one-shot `python -m edgmes.runtime` CLI;
- policy-before-backend enforcement;
- bounded ledger projection and immutable completion/verification updates;
- no executable tools or mutation authority in the edge profile.

A real Ollama smoke task completed with the 268.10M-parameter `functiongemma`
model (300 MB, 32K context). It returned a non-empty response and produced
three ledger entries. FunctionGemma is intentionally treated as a router/action
model; the smoke result does not establish it as a primary conversational model.
The previously attempted 1.9B Qwen3.5 model remains too large for this host and
was not used as a fallback.

### 4. Verification benchmark

Create a small reproducible benchmark covering:

1. inspect a project
2. diagnose a service
3. edit one file
4. run tests
5. recover from a failed command
6. perform a safe multi-step system task

Measure completion, unnecessary/invalid tool calls, context growth, recovery,
verification, latency, and destructive-action avoidance.

### 5. Packaging and synchronization

Only after the runtime boundary is stable:

- split edge/full dependency extras
- add clean editable installation checks
- add an edge package manifest and forbidden-import test
- automate upstream-sync PR creation
- classify protected runtime changes
- run edge smoke tests and dependency audits in CI

## Definition of done for the first usable Edgmes release

- `edgmes --help` starts without loading unrelated integrations.
- A supported local model completes a bounded file/task workflow.
- Tool exposure is profile-controlled before request construction.
- Context remains within the configured budget.
- Mutations have explicit verification or are rejected.
- Durable state survives a fresh process.
- Edge tests pass in a clean editable environment.
- An upstream sync can be opened as a PR without silently replacing Edgmes policy.
