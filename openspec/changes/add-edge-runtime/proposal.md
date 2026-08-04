## Why

Edgmes now has bounded model policies and state selection, but no runtime composes those contracts into a real local-model turn. A small provider-neutral runtime seam is needed to exercise the edge path without importing Hermes' broad conversation loop.

## What Changes

- Add an injected chat-backend protocol and Ollama-compatible HTTP backend.
- Add a bounded runtime that resolves a capability policy before every request.
- Select ledger context under the model profile budget and append the current request.
- Record the response and verification state in an immutable ledger snapshot.
- Add a CLI entry point for one-shot local edge tasks.

## Capabilities

### New Capabilities

- `edge-runtime`: Execute bounded one-shot local-model turns through explicit policy and ledger seams.

### Modified Capabilities

- None.

## Impact

- New provider-neutral runtime module and CLI entry point under `edgmes/`.
- No new Python dependency; Ollama transport uses the standard library.
- Tests use a fake backend; one live smoke test exercises the configured local Ollama service.
