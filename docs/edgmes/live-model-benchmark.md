# Edgmes live comparative benchmark

`scripts/benchmarks/live_model_benchmark.py` measures a model's bounded plan
completion for the six Edgmes task classes at **16,000, 32,000, 48,000, and
64,000 token** context budgets. It does not execute model-proposed commands;
the deterministic verification benchmark remains the execution and safety
baseline.

## Configure an OpenAI-compatible backend

The endpoint must expose `POST {base-url}/chat/completions`. Credentials are
read only from the environment and are never written to the JSON report.

```bash
export EDGMES_API_KEY=...
uv run --locked python scripts/benchmarks/live_model_benchmark.py \
  --base-url https://your-endpoint.example/v1 \
  --model your-model --output /tmp/edgmes-live.json
```

Use another secret variable without putting the secret on the command line:

```bash
EDGMES_API_KEY=... python scripts/benchmarks/live_model_benchmark.py \
  --api-key-env OPENAI_API_KEY --case-limit 1
```

The default run makes 24 requests (six cases at each budget). `--case-limit 1`
is a bounded connectivity smoke test. `--levels 16000,32000` is useful for a
shorter comparison. Each result includes status, completion and verification
flags, tool-call count, latency, prompt/response sizes, estimated context
usage, parsed plan, and a failure reason where relevant.

## Offline and unavailable behavior

No credentials are assumed. With no configured key, the command still emits a
complete machine-readable report: every requested case is `status: "unavailable"`,
`completion: false`, `verification: false`, and no synthetic plan or score is
created. The summary separates `passed`, `failed`, and `unavailable`; the CLI
returns exit code 1 when either failed or unavailable results exist. This makes
an offline run honest and CI-detectable rather than silently treating it as a
passing benchmark.

Network errors, HTTP errors, empty responses, and invalid backend responses are
also recorded as unavailable. A reachable backend that returns malformed model
JSON is recorded as `failed`. Inject `CompletionClient` into `run()` for tests
or another provider; no provider SDK is required.

## Interpretation

The context is synthetic and uses an approximately four-characters-per-token
fixture expansion. `context_tokens` is the requested budget, while
`context_tokens_estimate` is a reporting estimate—not a tokenizer-accurate
claim. Compare reports only when the model, endpoint configuration, benchmark
version, case definitions, and requested levels are recorded consistently.
