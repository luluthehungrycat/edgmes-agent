# Bounded context and state ledger

Edgmes keeps raw Hermes transcript/session persistence separate from the compact
state projection sent to constrained models.

`LedgerEntry` represents structured state such as:

- durable facts and identity;
- current goal and constraints;
- evidence and verification state;
- completed/failed actions;
- changed artifacts and next action;
- the current request.

Entries are immutable, have stable IDs, reject transcript-like and secret-like
content, and are grouped in immutable `StateLedger` snapshots. Appending returns a
new snapshot rather than mutating the existing one.

`select_bounded_context(entries, budget=...)` ranks entries by mandatory status,
verification, priority, recency, and stable ID. It greedily includes complete
entries until the measured budget is full. Mandatory current-request context must
fit or selection fails; lower-priority optional entries are reported in `omitted`,
with stable `omission_reasons` metadata. The same inputs always produce the same
`ContextProjection`.

An optional injected tokenizer receives the exact rendered context and must return
a positive integer. Missing, failing, or invalid adapters use the conservative
character-count fallback (`measurement_mode == "character-fallback"`). `EdgeRuntime`
passes the system instruction and separators as wrapper text, so the count covers
exactly what is rendered for the backend without changing `ChatBackend`. The
projection reports `measured_count` and `measurement_mode`. No tokenizer package,
model-name heuristic, or network lookup is used; 16K/32K/48K/64K are ordinary
artificial test budgets.
