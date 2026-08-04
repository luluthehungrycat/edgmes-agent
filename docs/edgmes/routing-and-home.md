# Edgmes routing and home layout

## Routing contract

Edgmes resolves a task using this precedence:

```text
explicit profile
    ↓ if absent
 deterministic classifier
    ↓ if ambiguous
 local FunctionGemma-compatible router
    ↓ if unavailable/invalid/uncertain
 configured larger-model escalation
    ↓ if unavailable/uncertain
 unresolved result
```

The local router receives only a compact profile catalog. It returns a validated
profile identifier and confidence; it cannot add tools, invoke escalation, or
bypass approvals. The selected specialist receives the original request plus a
bounded state handoff and only its profile's tools.

FunctionGemma is optional. The core Edgmes package does not import a model
runtime, download weights, or require Transformers/llama.cpp. A future runtime
can inject a generator into `FunctionGemmaRouter`.

## Independent home

Edgmes defaults to:

```text
~/.edgmes/
├── config/
├── state/
│   └── sessions/
├── skills/
├── cache/
├── logs/
└── runtime/
```

Set `EDGMES_HOME` to an absolute path to override the root. Edgmes does not
implicitly inspect or write `~/.hermes`; migration must be an explicit future
operation.

The current change provides contracts and policy only. It does not yet expose a
full `edgmes` CLI or execute specialist models. Those integrations belong to the
next runtime change.
