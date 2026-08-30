## 1. Benchmark contract

- [x] 1.1 Define the provider-neutral backend, standard context budgets, result statuses, and multidimensional metrics.
- [x] 1.2 Implement OpenAI-compatible endpoint configuration without persisting credentials.

## 2. Honest execution and reporting

- [x] 2.1 Emit one machine-readable result per case and budget with latency, completion, verification, tool-call, and context metrics.
- [x] 2.2 Record unavailable backends separately from malformed model responses without fabricated plans.

## 3. Verification and guidance

- [x] 3.1 Add injected-backend regression coverage and preserve compatibility with the existing benchmark tests.
- [x] 3.2 Document live configuration, offline behavior, output fields, and exit codes.
- [x] 3.3 Run focused tests, offline invocation, strict OpenSpec validation, and diff checks.
