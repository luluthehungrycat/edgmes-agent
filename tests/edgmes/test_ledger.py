from dataclasses import FrozenInstanceError

import pytest

from edgmes.ledger import (
    ContextBudgetError,
    LedgerEntry,
    LedgerError,
    StateLedger,
    select_bounded_context,
)


def entry(entry_id: str, content: str, **overrides: object) -> LedgerEntry:
    values: dict[str, object] = {
        "entry_id": entry_id,
        "category": "evidence",
        "content": content,
        "priority": 1,
        "recency": 1,
    }
    values.update(overrides)
    return LedgerEntry(**values)


def test_ledger_accepts_structured_categories_and_returns_new_snapshots() -> None:
    ledger = StateLedger()
    updated = ledger.append(entry("goal", "Inspect the project", category="current_goal"))

    assert ledger.entries == ()
    assert updated.entries[0].category == "current_goal"


def test_entry_rejects_transcript_and_secret_like_state() -> None:
    with pytest.raises(LedgerError):
        entry("history", "raw messages", category="transcript")
    with pytest.raises(LedgerError):
        entry("secret", "token=redacted", metadata={"credential": "[REDACTED]"})


def test_selector_prioritizes_mandatory_verified_and_priority_items() -> None:
    result = select_bounded_context(
        [
            entry("stale", "stale", priority=9, recency=1),
            entry("verified", "verified", priority=1, verified=True, recency=1),
            entry("request", "request", mandatory=True, category="current_request"),
        ],
        budget=15,
    )

    assert tuple(item.entry_id for item in result.selected) == ("request", "verified")
    assert result.serialized_size == 15
    assert result.omitted == ("stale",)


def test_selector_is_stable_and_does_not_mutate_inputs() -> None:
    candidates = [entry("b", "B", priority=1), entry("a", "A", priority=1)]
    first = select_bounded_context(candidates, budget=1)
    second = select_bounded_context(candidates, budget=1)

    assert first == second
    assert [item.entry_id for item in candidates] == ["b", "a"]


def test_mandatory_item_that_does_not_fit_is_rejected() -> None:
    with pytest.raises(ContextBudgetError):
        select_bounded_context(
            [entry("request", "too large", mandatory=True, category="current_request")],
            budget=2,
        )


def test_ledger_entries_are_immutable() -> None:
    value = entry("fact", "A fact")
    with pytest.raises(FrozenInstanceError):
        value.content = "changed"  # type: ignore[misc]
