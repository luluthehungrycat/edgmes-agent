# Edgmes architecture

## Initial boundary

Edgmes begins as a downstream namespace layered onto the unmodified Hermes
Agent tree:

```text
upstream Hermes tree
├── agent/
├── tools/
├── gateway/
├── plugins/
└── hermes_cli/

Edgmes additions
├── edgmes/
├── tests/edgmes/
├── docs/edgmes/
└── scripts/upstream/
```

Do not duplicate `agent/`, `tools/`, or the conversation loop while the
runtime seams are still being established.

## Intended execution policy

The future edge runtime should resolve a model capability profile before
constructing the request:

```text
model profile + task class
        ↓
capability and tool policy
        ↓
bounded context selection
        ↓
edge execution loop
        ↓
verification and state-ledger update
```

The first implementation should reuse Hermes' providers, sessions, approvals,
file-safety mechanisms, memory format, skills format, and context-engine
interfaces wherever those interfaces are suitable.

## Non-goals for the first milestone

- no rewrite of `agent/conversation_loop.py`
- no broad tool removal from the upstream tree
- no premature package split
- no automatic model capability assumptions based only on parameter count
- no new background services
