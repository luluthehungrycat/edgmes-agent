# Edgmes runtime

The first runtime milestone is intentionally a bounded one-shot turn rather than
a replacement for Hermes' full conversation loop.

```bash
python3 -m edgmes.runtime \
  --model jaahas/qwen3.5-uncensored:2b \
  "Reply with one short sentence: what is Edgmes?"
```

The CLI defaults to the local Ollama endpoint at `http://127.0.0.1:11434` and
the smallest configured local model. Override them with `--base-url` and
`--model`, or `EDGMES_OLLAMA_URL` and `EDGMES_MODEL`. One invocation makes one
non-streaming backend request; there is no fallback model chain.

Runtime order:

1. create a mandatory current-request ledger entry;
2. select prior structured state under the profile's context budget;
3. resolve the pure capability policy before backend access;
4. send only a system instruction and bounded projection to the injected backend;
5. record completed-action and verified-response state in a new immutable ledger
   snapshot.

`OllamaBackend` is a small standard-library adapter. `ChatBackend` is the
provider-neutral protocol, so tests and future local transports do not require
an SDK dependency. Model text is treated as untrusted output: this milestone
exposes no executable tools or mutation path.

Use `--json` to inspect the selected model, profile, context IDs, backend evidence,
and ledger-entry count without exposing raw internal state.
