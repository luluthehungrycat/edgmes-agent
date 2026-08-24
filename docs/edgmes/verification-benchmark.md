# Edgmes verification benchmark

`verification_benchmark.py` is a versioned, offline benchmark for the Edgmes
runtime safety and plumbing contract. It uses a fresh temporary fixture for
every case and never reads or mutates the repository checkout.

## Run it

From the repository root:

```bash
python3 scripts/benchmarks/verification_benchmark.py --json
```

Write the JSON report to a file:

```bash
python3 scripts/benchmarks/verification_benchmark.py \
  --json --output /tmp/edgmes-verification.json
```

The current version is `edgmes-verification-v1` and contains six cases:

- `inspect-project`: read fixture project information without changing the tree;
- `diagnose-service`: observe a failing service and identify its fixture diagnosis;
- `edit-one-file`: edit one file and verify its exact postcondition;
- `run-tests`: execute the fixture test command and verify its result;
- `recover-command`: recover from one failed command using known fixture state;
- `safe-multi-step`: perform an approved write in an isolated workspace and verify it.

Each case reports completion, invalid/unnecessary tool calls, context growth,
recovery attempts, verification, latency, destructive-action avoidance, evidence,
and a failure reason when applicable.

## Interpreting results

The default `deterministic-fixture` executor is an offline reference executor.
A 100% result proves that the benchmark harness, fixture isolation, postconditions,
and reporting path work; it is not a claim about local-model quality. Live model
executors should identify their model, profile, and configuration in the report
before results are compared.

The benchmark intentionally uses isolated temporary directories. The
`safe-multi-step` case is the only case with an expected mutation, and its target
must remain inside that case's fixture.
