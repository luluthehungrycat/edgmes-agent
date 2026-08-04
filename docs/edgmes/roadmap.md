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

**Status:** namespace and documentation scaffold complete.

Next, measure the inherited runtime before optimizing it:

- process/import startup time
- provider/model initialization time
- tool discovery and construction time
- system-prompt assembly time and token/character size
- skill-index and memory assembly cost
- first-token latency
- tool-call latency and result size
- context-compression behavior

The baseline must run without modifying upstream runtime behavior.

### 1. Capability profiles

Add a small, serializable capability model under `edgmes/`:

- context and input/output budgets
- maximum steps and tool calls
- allowed toolsets/tools
- retry limits
- delegation and parallelism policy
- compression policy
- verification requirements

Add a pure resolver that maps `(model metadata, task class, configured profile)`
to a bounded policy. Test this before wiring it into the agent loop.

Initial profiles:

```text
nano          0.3–2B   one-shot/read-only actions
small         3–4B     short bounded chains
medium-edge   ~7B      modest coding/troubleshooting workflows
full          remote/larger models; inherited Hermes behavior
```

### 2. Bounded context and state ledger

Use the existing context-engine seam where possible. Add Edgmes interfaces for:

- identity and durable user facts
- current goal and constraints
- relevant evidence
- completed and failed actions
- changed artifacts
- verification state
- next recommended action

The raw transcript remains persisted; the model receives a bounded projection.
Add deterministic compaction before auxiliary-model summarization.

### 3. Edge tool policy and runtime

Add lazy, policy-driven tool construction. The edge runtime should initially
prefer a small set such as:

- `read_file`
- `search_files`
- `write_file`
- `patch`
- `terminal`
- `process`

Delegation, MCP, browser/computer use, cron, media, and broad plugin discovery
remain disabled by default in edge profiles.

Add an explicit `edgmes` entry point only once the policy can run one real task.

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
