# Inherited Hermes baseline harness

Run from the repository root:

```bash
python3 scripts/benchmarks/baseline_harness.py --iterations 3 --pretty
```

The harness uses fresh Python subprocesses and a temporary `HERMES_HOME` for
each invocation. It does not call a model provider, access credentials, or
modify the checkout.

It reports four phases:

- `startup_import`: cold import of `run_agent`
- `prompt_assembly`: skill-index and context-file prompt preparation
- `tool_discovery_construction`: built-in tool module discovery and registry construction
- `representative_read_only_task`: bounded inspection of `README_EDGMES.md`

Each phase reports individual samples, median/min/max latency, and output
cardinality. The representative task is deliberately provider-free; it is a
harness-preparation baseline, not an end-to-end model-quality benchmark.

Save a run for comparison with:

```bash
python3 scripts/benchmarks/baseline_harness.py --pretty > baseline.json
```

Compare Edgmes changes against the same machine, Python version, dependency
lock, and iteration count. Keep model time-to-first-byte and tool execution
latency as separate future measurements.
