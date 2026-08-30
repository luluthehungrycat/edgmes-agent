"""Structured state ledger values and deterministic bounded context selection."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import tempfile
from types import MappingProxyType
from typing import Iterable, Mapping, Protocol


class LedgerError(ValueError):
    """A ledger entry or snapshot violates the bounded state contract."""


class ContextBudgetError(LedgerError):
    """Mandatory context cannot fit within the requested budget."""


class Tokenizer(Protocol):
    """Optional provider-shaped counter for already-rendered context text."""

    def __call__(self, text: str) -> int: ...


@dataclass(frozen=True)
class MeasurementResult:
    """Validated count and its accounting mode."""

    count: int
    mode: str


def measure_text(text: str, tokenizer: Tokenizer | None = None) -> MeasurementResult:
    """Measure text, falling back conservatively to characters on adapter errors."""

    if tokenizer is not None:
        try:
            count = tokenizer(text)
            if isinstance(count, int) and not isinstance(count, bool) and count > 0:
                return MeasurementResult(count, "tokenizer")
        except Exception:  # adapters are optional and must never break budgeting
            pass
    count = len(text)
    return MeasurementResult(count, "character-fallback")


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

    def as_dict(self) -> dict[str, object]:
        """Return the versioned, JSON-safe persistence representation."""

        return {
            "format_version": 1,
            "entries": [
                {
                    "entry_id": item.entry_id,
                    "category": item.category,
                    "content": item.content,
                    "priority": item.priority,
                    "recency": item.recency,
                    "verified": item.verified,
                    "mandatory": item.mandatory,
                    "metadata": dict(item.metadata),
                }
                for item in self.entries
            ],
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "StateLedger":
        """Validate and construct a ledger from persisted JSON data."""

        entries_value = value.get("entries")
        if value.get("format_version") != 1 or not isinstance(entries_value, list):
            raise LedgerError("unsupported or malformed ledger format")
        entries: list[LedgerEntry] = []
        for raw in entries_value:
            if not isinstance(raw, Mapping):
                raise LedgerError("ledger entry must be an object")
            try:
                entries.append(
                    LedgerEntry(
                        entry_id=raw["entry_id"],
                        category=raw["category"],
                        content=raw["content"],
                        priority=raw.get("priority", 0),
                        recency=raw.get("recency", 0),
                        verified=raw.get("verified", False),
                        mandatory=raw.get("mandatory", False),
                        metadata=raw.get("metadata", {}),
                    )
                )
            except (AttributeError, KeyError, TypeError, ValueError) as exc:
                raise LedgerError("malformed ledger entry") from exc
        return cls(tuple(entries))

    def save(self, path: str | Path) -> None:
        """Atomically persist this snapshot as JSON."""

        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.as_dict(), handle, ensure_ascii=False, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @classmethod
    def load(cls, path: str | Path) -> "StateLedger":
        """Load and validate a persisted snapshot."""

        try:
            value = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LedgerError("unable to load ledger") from exc
        if not isinstance(value, Mapping):
            raise LedgerError("ledger root must be an object")
        return cls.from_dict(value)


@dataclass(frozen=True)
class ContextProjection:
    """Selected context plus deterministic omission metadata."""

    selected: tuple[LedgerEntry, ...]
    omitted: tuple[str, ...]
    budget: int
    measured_count: int = 0
    measurement_mode: str = "character-fallback"
    omission_reasons: Mapping[str, str] = field(default_factory=dict)
    _rendered_context: str = ""

    @property
    def serialized_size(self) -> int:
        return len(self.rendered_text)

    @property
    def rendered_text(self) -> str:
        return "\n\n".join(f"[{item.category}]\n{item.content}" for item in self.selected)

    @property
    def rendered_context(self) -> str:
        """The exact text measured for this projection."""

        return self._rendered_context or self.rendered_text


def _rendered_entry_size(item: LedgerEntry) -> int:
    return len(f"[{item.category}]\n{item.content}")


def select_bounded_context(
    entries: Iterable[LedgerEntry], *, budget: int, tokenizer: Tokenizer | None = None,
    prefix: str = "", suffix: str = ""
) -> ContextProjection:
    """Select whole entries deterministically within a measured rendered budget.

    ``prefix`` and ``suffix`` let callers account for wrapper text (notably the
    system instruction) without changing the backend protocol. With no
    tokenizer or wrapper this retains the historical character-budget API.
    """

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
    omission_reasons: dict[str, str] = {}

    def rendered(items: Iterable[LedgerEntry]) -> str:
        body = "\n\n".join(f"[{item.category}]\n{item.content}" for item in items)
        return f"{prefix}{body}{suffix}"

    measured = measure_text(rendered(()), tokenizer)
    for item in ranked:
        candidate = tuple(selected) + (item,)
        next_measurement = measure_text(rendered(candidate), tokenizer)
        if next_measurement.count <= budget:
            selected.append(item)
            measured = next_measurement
        elif item.mandatory:
            raise ContextBudgetError(f"mandatory context does not fit: {item.entry_id}")
        else:
            omitted.append(item.entry_id)
            omission_reasons[item.entry_id] = "budget"
    # Re-measure the final rendered value so metadata and diagnostics always
    # describe the exact context that will be sent, not a rejected candidate.
    measured = measure_text(rendered(selected), tokenizer)
    if measured.count > budget:
        raise ContextBudgetError("selected context exceeds budget")
    return ContextProjection(
        tuple(selected), tuple(omitted), budget, measured.count, measured.mode,
        MappingProxyType(omission_reasons), rendered(selected),
    )
