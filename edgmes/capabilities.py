"""Immutable model capability profiles and pure tool/context policy resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from types import MappingProxyType
from typing import Any, Iterable, Mapping


class CapabilityProfileError(ValueError):
    """A capability profile or policy request is invalid."""


class UnknownCapabilityProfileError(CapabilityProfileError):
    """A policy references a profile outside the registry snapshot."""


_SECRET_MARKERS = (
    "api_key",
    "apikey",
    "authorization",
    "connection_string",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def _validate_identifier(value: str, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[a-z][a-z0-9._/-]*", value):
        raise CapabilityProfileError(f"invalid {label}: {value!r}")


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
class ModelCapabilityProfile:
    """An immutable, provider-independent execution limit for one model tier."""

    id: str
    description: str
    context_budget: int
    output_budget: int
    capabilities: frozenset[str] = field(default_factory=frozenset)
    permitted_tools: frozenset[str] = field(default_factory=frozenset)
    max_steps: int = 1
    max_tool_calls: int = 1
    allow_mutation: bool = False
    supports_tool_calling: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_identifier(self.id, "profile id")
        if not isinstance(self.description, str) or not self.description.strip():
            raise CapabilityProfileError("profile description must not be empty")
        for label, value in (
            ("context_budget", self.context_budget),
            ("output_budget", self.output_budget),
            ("max_steps", self.max_steps),
            ("max_tool_calls", self.max_tool_calls),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise CapabilityProfileError(f"{label} must be a positive integer")
        for capability in self.capabilities:
            _validate_identifier(capability, "capability")
        for tool in self.permitted_tools:
            _validate_identifier(tool, "tool")
        if _contains_secret_marker(self.metadata):
            raise CapabilityProfileError("profile metadata contains secret-like content")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "permitted_tools", frozenset(self.permitted_tools))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class CapabilityProfileRegistry:
    """Immutable snapshot of enabled model capability profiles."""

    def __init__(self, profiles: Iterable[ModelCapabilityProfile]) -> None:
        values = tuple(profiles)
        ids = [profile.id for profile in values]
        if len(set(ids)) != len(ids):
            raise CapabilityProfileError("profile ids must be unique")
        self._profiles = MappingProxyType({profile.id: profile for profile in values})

    def get(self, profile_id: str) -> ModelCapabilityProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise UnknownCapabilityProfileError(f"unknown capability profile: {profile_id}") from exc

    def __contains__(self, profile_id: str) -> bool:
        return profile_id in self._profiles

    def __iter__(self):
        return iter(self._profiles.values())

    def catalog(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "id": profile.id,
                "description": profile.description,
                "context_budget": profile.context_budget,
                "output_budget": profile.output_budget,
                "capabilities": tuple(sorted(profile.capabilities)),
                "permitted_tools": tuple(sorted(profile.permitted_tools)),
                "max_steps": profile.max_steps,
                "max_tool_calls": profile.max_tool_calls,
                "supports_tool_calling": profile.supports_tool_calling,
            }
            for profile in self
        )


@dataclass(frozen=True)
class PolicyRequest:
    """Immutable request presented to the pure policy resolver."""

    required_capabilities: frozenset[str] = field(default_factory=frozenset)
    required_tools: frozenset[str] = field(default_factory=frozenset)
    optional_tools: frozenset[str] = field(default_factory=frozenset)
    estimated_context: int = 0
    requested_output: int = 0
    requested_steps: int = 0
    requested_tool_calls: int = 0
    requires_mutation: bool = False
    mutation_approved: bool = False

    def __post_init__(self) -> None:
        for label, values in (
            ("required_capabilities", self.required_capabilities),
            ("required_tools", self.required_tools),
            ("optional_tools", self.optional_tools),
        ):
            for value in values:
                _validate_identifier(value, label[:-1])
        for label, value in (
            ("estimated_context", self.estimated_context),
            ("requested_output", self.requested_output),
            ("requested_steps", self.requested_steps),
            ("requested_tool_calls", self.requested_tool_calls),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise CapabilityProfileError(f"{label} must be a non-negative integer")
        object.__setattr__(self, "required_capabilities", frozenset(self.required_capabilities))
        object.__setattr__(self, "required_tools", frozenset(self.required_tools))
        object.__setattr__(self, "optional_tools", frozenset(self.optional_tools))


@dataclass(frozen=True)
class PolicyDecision:
    """Pure resolver output; rejected decisions never expose executable tools."""

    status: str
    profile_id: str
    permitted_tools: tuple[str, ...] = ()
    filtered_optional_tools: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    max_context: int = 0
    max_output: int = 0
    max_steps: int = 0
    max_tool_calls: int = 0

    @property
    def allowed(self) -> bool:
        return self.status == "allowed"


def resolve_tool_context_policy(
    profile: ModelCapabilityProfile, request: PolicyRequest
) -> PolicyDecision:
    """Resolve a request without model, filesystem, credential, or global-state access."""

    reasons: list[str] = []
    required_capabilities = sorted(request.required_capabilities - profile.capabilities)
    reasons.extend(f"capability:{item}" for item in required_capabilities)
    required_tools = sorted(request.required_tools - profile.permitted_tools)
    reasons.extend(f"required_tool:{item}" for item in required_tools)
    filtered_optional = sorted(request.optional_tools - profile.permitted_tools)

    budgets = (
        ("estimated_context", request.estimated_context, profile.context_budget),
        ("requested_output", request.requested_output, profile.output_budget),
        ("requested_steps", request.requested_steps, profile.max_steps),
        ("requested_tool_calls", request.requested_tool_calls, profile.max_tool_calls),
    )
    reasons.extend(f"{label}:{value}>{limit}" for label, value, limit in budgets if value > limit)
    if request.requires_mutation and (not profile.allow_mutation or not request.mutation_approved):
        reasons.append("mutation:approval-required")

    if reasons:
        return PolicyDecision(
            status="rejected",
            profile_id=profile.id,
            reasons=tuple(reasons),
            max_context=profile.context_budget,
            max_output=profile.output_budget,
            max_steps=profile.max_steps,
            max_tool_calls=profile.max_tool_calls,
        )

    permitted = tuple(sorted(request.required_tools | (request.optional_tools & profile.permitted_tools)))
    return PolicyDecision(
        status="allowed",
        profile_id=profile.id,
        permitted_tools=permitted,
        filtered_optional_tools=tuple(filtered_optional),
        max_context=profile.context_budget,
        max_output=min(request.requested_output or profile.output_budget, profile.output_budget),
        max_steps=min(request.requested_steps or profile.max_steps, profile.max_steps),
        max_tool_calls=min(request.requested_tool_calls or profile.max_tool_calls, profile.max_tool_calls),
    )
