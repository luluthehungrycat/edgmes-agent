## Context

The current script already generates synthetic context and parses a bounded JSON plan, but its OpenRouter-only client raises on missing credentials and reports only pass/fail. See proposal.md and the live-comparative-benchmark spec for the observable contract.

## Goals / Non-Goals

**Goals:** preserve the injected-client seam, support any OpenAI-compatible chat endpoint, retain one result per request, and make unavailable/offline operation inspectable and CI-detectable.

**Non-Goals:** executing model actions, adding provider SDK dependencies, claiming tokenizer-accurate context usage, or changing the Edgmes runtime.

## Decisions

- Keep a small `CompletionClient` protocol and accept response metadata so tests and future providers can inject a backend without credentials.
- Use the standard-library HTTP client for `/chat/completions`; the endpoint and model are configurable while the key is selected by an environment-variable name.
- Classify missing keys, transport errors, HTTP errors, and invalid provider envelopes as unavailable; classify malformed model plan JSON as failed. Never synthesize a plan for either state.
- Use explicit top-level summary counts and per-result fields rather than a scalar score. Tool calls come from provider metadata when available and otherwise from parsed requested actions.

## Risks / Trade-offs

- [Risk] Synthetic context is only an estimate → report requested and estimated context separately and document the limitation.
- [Risk] A remote provider can reject 64K requests → record the affected request as unavailable instead of reducing the budget silently.
- [Risk] Error bodies may contain sensitive provider details → cap error text and never include request headers or key values.

## Migration Plan

The existing command remains the entry point; users with the old OpenRouter variable can pass `--api-key-env OPENROUTER_API_KEY`. Existing injected-client tests continue to work. Rollback is deleting the new live harness changes; the deterministic benchmark is independent.
