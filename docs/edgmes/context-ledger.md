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
entries until the character budget is full. Mandatory current-request context must
fit or selection fails; lower-priority optional entries are reported in `omitted`.
The same inputs always produce the same `ContextProjection`.

The selector currently budgets characters rather than tokenizer-specific tokens.
The future edge runtime will translate model budgets conservatively before calling
this interface.
