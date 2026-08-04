"""Structured state ledger values and deterministic bounded context selection."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping


class LedgerError(ValueError):
    """A ledger entry or snapshot violates the bounded state contract."""


class ContextBudgetError(LedgerError):
    """Mandatory context cannot fit within the requested budget."""


_ALLOWED_CATEGORIES = frozenset(
    {
        "identity",
        "durable_fact",
        "current_goal",
        "constraint",
        "evidence",
        "completed_action",
        "failed_action",
        "changed_artifact",
        "verification",
        "next_action",
        "current_request",
    }
)
_SECRET_MARKERS = (
    "api_key",
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def _contains_secret_marker(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            any(marker in str(key).casefold() for marker in _SECRET_MARKERS)
            or _contains_secret_marker(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_secret_marker(item) for item in value)
    return any(marker in str(value).casefold() for marker in _SECRET_MARKERS)


@dataclass(frozen=True)
class LedgerEntry:
    """One immutable, model-facing state fact or task observation."""

    entry_id: str
    category: str
    content: str
    priority: int = 0
    recency: int = 0
    verified: bool = False
    mandatory: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.entry_id.strip() or any(char.isspace() for char in self.entry_id):
            raise LedgerError("entry_id must be non-empty and whitespace-free")
        if self.category not in _ALLOWED_CATEGORIES:
            raise LedgerError(f"unsupported ledger category: {self.category!r}")
        if not self.content.strip():
            raise LedgerError("ledger content must not be empty")
        if len(self.content) > 16_384:
            raise LedgerError("ledger content exceeds the entry limit")
        if not isinstance(self.priority, int) or self.priority < 0:
            raise LedgerError("priority must be a non-negative integer")
        if not isinstance(self.recency, int) or self.recency < 0:
            raise LedgerError("recency must be a non-negative integer")
        if _contains_secret_marker(self.content) or _contains_secret_marker(self.metadata):
            raise LedgerError("ledger entry contains secret-like content")
        if self.category == "current_request":
            object.__setattr__(self, "mandatory", True)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class StateLedger:
    """Persistent-friendly immutable snapshot of structured state entries."""

    entries: tuple[LedgerEntry, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(self.entries)
        identifiers = [entry.entry_id for entry in values]
        if len(set(identifiers)) != len(identifiers):
            raise LedgerError("ledger entry ids must be unique")
        object.__setattr__(self, "entries", values)

    def append(self, entry: LedgerEntry) -> "StateLedger":
        if entry.entry_id in {item.entry_id for item in self.entries}:
            raise LedgerError(f"duplicate ledger entry: {entry.entry_id}")
        return StateLedger(self.entries + (entry,))


@dataclass(frozen=True)
class ContextProjection:
    """Selected context plus deterministic omission metadata."""

    selected: tuple[LedgerEntry, ...]
    omitted: tuple[str, ...]
    budget: int

    @property
    def serialized_size(self) -> int:
        return sum(len(item.content) for item in self.selected)


def select_bounded_context(
    entries: Iterable[LedgerEntry], *, budget: int
) -> ContextProjection:
    """Select whole ledger entries deterministically within a character budget."""

    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
        raise ContextBudgetError("context budget must be a positive integer")
    candidates = tuple(entries)
    identifiers = [entry.entry_id for entry in candidates]
    if len(set(identifiers)) != len(identifiers):
        raise LedgerError("context entry ids must be unique")
    ranked = tuple(
        sorted(
            candidates,
            key=lambda item: (
                not item.mandatory,
                not item.verified,
                -item.priority,
                -item.recency,
                item.entry_id,
            ),
        )
    )
    selected: list[LedgerEntry] = []
    omitted: list[str] = []
    size = 0
    for item in ranked:
        next_size = size + len(item.content)
        if next_size <= budget:
            selected.append(item)
            size = next_size
        elif item.mandatory:
            raise ContextBudgetError(f"mandatory context does not fit: {item.entry_id}")
        else:
            omitted.append(item.entry_id)
    return ContextProjection(tuple(selected), tuple(omitted), budget)
