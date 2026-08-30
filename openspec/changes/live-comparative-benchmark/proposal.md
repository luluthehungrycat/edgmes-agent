## Why

The existing live benchmark only supports one provider-specific configuration and fails before producing evidence when credentials are absent. A comparative benchmark needs all four Edgmes context budgets, provider-neutral injection, and an honest machine-readable distinction between passed, failed, and unavailable runs.

## What Changes

- Add a provider-neutral completion backend contract and OpenAI-compatible HTTP adapter.
- Run every selected case at 16K, 32K, 48K, and 64K token budgets by default.
- Report completion, verification, tool-call, context-size, latency, and backend status metrics per request.
- Emit unavailable results without fabricated plans when credentials or the backend are unavailable.
- Document configuration, offline behavior, and exit-code semantics.

## Capabilities

### New Capabilities
- `live-comparative-benchmark`: Run and report comparative live model evaluations across context budgets.

### Modified Capabilities

## Impact

Affects `scripts/benchmarks/live_model_benchmark.py`, its Edgmes tests, and live benchmark documentation. The adapter uses only the Python standard library and reads credentials from an environment variable; it does not change the agent runtime or persist secrets.
