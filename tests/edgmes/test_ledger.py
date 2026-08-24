from dataclasses import FrozenInstanceError
import json

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
        budget=46,
    )

    assert tuple(item.entry_id for item in result.selected) == ("request", "verified")
    assert result.serialized_size == 46
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


def test_ledger_round_trips_through_versioned_json(tmp_path) -> None:
    original = StateLedger((entry("fact", "A verified fact", verified=True),))
    path = tmp_path / "state" / "ledger.json"

    original.save(path)
    restored = StateLedger.load(path)

    assert restored == original
    assert json.loads(path.read_text(encoding="utf-8"))["format_version"] == 1


def test_ledger_rejects_malformed_persisted_data(tmp_path) -> None:
    path = tmp_path / "ledger.json"
    path.write_text('{"format_version": 1, "entries": [{"entry_id": "x"}]}', encoding="utf-8")

    with pytest.raises(LedgerError):
        StateLedger.load(path)
