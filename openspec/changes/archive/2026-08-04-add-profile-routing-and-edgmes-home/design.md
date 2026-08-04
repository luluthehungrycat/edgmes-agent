## Context

See `proposal.md` for motivation. The repository currently contains the inherited
Hermes tree plus an Edgmes namespace scaffold; no Edgmes runtime owns state or
routes requests yet. The design must remain importable without optional model
libraries and must not modify the inherited Hermes loop in this change.

## Goals / Non-Goals

**Goals:**

- Define a small Python API for profiles, routing decisions, and policy errors.
- Make deterministic routing the first operational path.
- Add an optional FunctionGemma-compatible router adapter behind a protocol;
  absence of the model or inference backend must be a normal fallback condition.
- Represent larger-model escalation as a harness callback, never as an
  unrestricted action exposed to the local router.
- Resolve an independent Edgmes home using `EDGMES_HOME` or `~/.edgmes`.
- Make routing and home resolution pure/testable where possible.

**Non-Goals:**

- Changing Hermes' conversation loop, registry, or tool implementations.
- Downloading model weights or adding a heavyweight ML dependency.
- Implementing actual specialist model execution in this change.
- Automatically importing Hermes profiles, memories, skills, credentials, or
  sessions.
- Supporting high-risk shopper/trader/computer-control execution by default.

## Decisions

### Profile registry is declarative and immutable at request time

Use typed profile metadata loaded from Edgmes-owned configuration. A request gets
a snapshot of the enabled registry; model output cannot add profiles or tools.
This makes profile selection auditable and prevents prompt-level capability
expansion.

Alternative rejected: letting the router emit arbitrary tool lists. That would
turn routing into an authorization boundary and make small-model mistakes more
dangerous.

### Routing uses a strict precedence chain

The routing coordinator evaluates:

1. explicit profile selection;
2. deterministic classifier;
3. local router adapter;
4. configured escalation callback;
5. unresolved result.

Each stage returns either a validated candidate or `abstain`. The next stage is
called only for abstention or invalid/low-confidence output.

Alternative rejected: always invoking FunctionGemma. That adds latency to easy
requests and makes the system dependent on an optional model.

### FunctionGemma is an adapter, not a dependency

Define a narrow router protocol accepting a compact profile catalog and returning
structured profile ID plus confidence. The adapter can call FunctionGemma using
its function-calling format, but the core package does not import Transformers,
llama.cpp, or any model runtime. The adapter is suitable for single-turn profile
selection; specialist execution remains outside this change.

Alternative rejected: treating FunctionGemma as the conversational primary. Its
role here is structured classification and action routing, not general dialogue.

### Escalation is an injected callback

The coordinator receives an optional escalation callable supplied by the eventual
runtime. The router cannot call it, choose arbitrary models, or pass credentials.
If absent, the coordinator returns `unresolved` with structured reasons.

This keeps policy and transport separate and lets a future runtime use a remote
model, a Hermes profile, or a human confirmation step.

### Context handoff is a data object

Define a serializable handoff containing the original request, selected profile,
constraints, bounded state, and routing metadata. It intentionally does not
contain the full transcript or unfiltered tool catalog. Specialist execution can
extend this object later without coupling the router to Hermes internals.

### Edgmes home resolution is explicit and fail-closed

Resolve `EDGMES_HOME` first, otherwise `Path.home() / ".edgmes"`. Require an
absolute path and expose named paths for config, state, sessions, skills, cache,
logs, and runtime metadata. The resolver does not inspect `~/.hermes` and does
not create directories until an explicit initialization call.

Alternative rejected: automatic fallback to `~/.hermes`. Co-existence and
security require a visible boundary; missing Edgmes state must remain missing.

## Risks / Trade-offs

- **[Risk]** A deterministic classifier can misroute ambiguous requests.  
  **Mitigation:** confidence thresholds, abstention, local router fallback, and
  larger-model escalation.

- **[Risk]** A FunctionGemma adapter may be unavailable or produce malformed
  output.  
  **Mitigation:** optional protocol, strict parsing, registry validation, and
  normal escalation/unresolved behavior.

- **[Risk]** One extra routing step increases latency.  
  **Mitigation:** explicit and deterministic paths bypass model routing; measure
  routing latency in the baseline harness.

- **[Risk]** Profile descriptions and routing metadata can leak sensitive task
  details.  
  **Mitigation:** bounded handoff, redacted audit events, and no credentials in
  routing input/output.

- **[Risk]** Future runtime integration may accidentally read Hermes state.  
  **Mitigation:** home isolation tests and a package-level rule that Edgmes
  resolution never falls back implicitly.

## Migration Plan

1. Add the Edgmes core types and home resolver without wiring them into Hermes.
2. Add deterministic routing and tests using in-memory profile definitions.
3. Add the optional local-router protocol and a parser-level FunctionGemma
   adapter test using mocked model output.
4. Add the escalation callback contract and unresolved behavior.
5. Integrate these interfaces into a future Edgmes runtime behind an explicit
   `edgmes` entry point.
6. Roll back by removing the new Edgmes runtime integration; inherited Hermes
   state and code remain untouched throughout.
