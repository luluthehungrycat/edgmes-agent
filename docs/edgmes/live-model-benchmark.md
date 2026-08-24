# Edgmes live model benchmark

`scripts/benchmarks/live_model_benchmark.py` measures whether an OpenAI-compatible
model can produce a bounded, verifiable plan for the six Edgmes task classes.
It does not execute model-proposed commands. The deterministic benchmark remains
the execution and safety baseline.

## OpenRouter

The default model is `liquid/lfm-2.5-2.6b:free`. It is currently the most
appropriate free remote baseline for this experiment because its published
context window is 65,536 tokens, so the full 16k/32k/48k/64k sweep fits its
advertised limit. The model is a capability probe, not a release-quality
agent recommendation.

```bash
export OPENROUTER_API_KEY=...
uv run --locked python scripts/benchmarks/live_model_benchmark.py \
  --output /tmp/edgmes-live.json
```

The default run makes 24 requests: six cases at each of four artificial context
levels. Use `--case-limit 1` for a connectivity smoke test. The report records
model, context level, latency, prompt/response size, parsed plan, and failures.

The context is deliberately synthetic and approximately four characters per
token. It tests prompt-budget behavior; it is not a tokenizer-accurate claim.

## Local model guidance

The development VPS has 7.8 GiB RAM, about 2 GiB available at inspection time,
and no swap. Existing 2–3B quantized Ollama models are reasonable for 16k
smoke tests. Running a new 7B model or attempting a 64k local sweep is not
worth the memory and latency risk on that host. Use the 24 GiB VPS or remote
inference for broader sweeps.
