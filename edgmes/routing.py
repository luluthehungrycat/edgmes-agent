"""Bounded specialist profiles and routing contracts for Edgmes."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping, Protocol, Sequence


class RoutingError(ValueError):
    """Base class for invalid routing requests or results."""


class UnknownProfileError(RoutingError):
    """A route referenced a profile outside the enabled registry."""


class PolicyError(RoutingError):
    """A route conflicts with capability, mutation, or risk policy."""


@dataclass(frozen=True)
class SpecialistProfile:
    id: str
    description: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    tools: tuple[str, ...] = ()
    model_policy: str = "default"
    max_steps: int = 1
    max_tool_calls: int = 1
    allow_mutation: bool = False
    require_verification: bool = True
    high_risk: bool = False

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z][a-z0-9-]*", self.id):
            raise ValueError(f"invalid profile id: {self.id!r}")
        if not self.description.strip():
            raise ValueError("profile description must not be empty")
        if self.max_steps < 1 or self.max_tool_calls < 1:
            raise ValueError("profile action limits must be positive")
        if len(set(self.tools)) != len(self.tools):
            raise ValueError("profile tools must be unique")
        if self.high_risk and self.allow_mutation is False:
            raise ValueError("high-risk profiles must declare their mutation policy")


class ProfileRegistry:
    """Immutable-at-request-time registry of enabled specialist profiles."""

    def __init__(self, profiles: Iterable[SpecialistProfile]) -> None:
        values = tuple(profiles)
        ids = [profile.id for profile in values]
        if len(set(ids)) != len(ids):
            raise ValueError("profile ids must be unique")
        self._profiles = MappingProxyType({profile.id: profile for profile in values})

    def get(self, profile_id: str) -> SpecialistProfile:
        try:
            return self._profiles[profile_id]
        except KeyError as exc:
            raise UnknownProfileError(f"unknown profile: {profile_id}") from exc

    def __contains__(self, profile_id: str) -> bool:
        return profile_id in self._profiles

    def __iter__(self):
        return iter(self._profiles.values())

    def catalog(self) -> tuple[dict[str, object], ...]:
        return tuple(
            {
                "id": profile.id,
                "description": profile.description,
                "capabilities": sorted(profile.capabilities),
            }
            for profile in self
        )


@dataclass(frozen=True)
class RouteCandidate:
    profile_id: str
    confidence: float
    source: str
    reason: str = ""
    required_capabilities: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("route confidence must be between 0 and 1")


@dataclass(frozen=True)
class RouteDecision:
    status: str
    source: str
    profile_id: str | None = None
    confidence: float = 0.0
    reason: str = ""
    candidates: tuple[str, ...] = ()
    escalated: bool = False

    @property
    def selected(self) -> bool:
        return self.status == "selected" and self.profile_id is not None


@dataclass(frozen=True)
class SpecialistHandoff:
    user_request: str
    profile_id: str
    tools: tuple[str, ...]
    state: Mapping[str, Any]
    constraints: tuple[str, ...]
    routing: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "state", MappingProxyType(dict(self.state)))
        object.__setattr__(self, "routing", MappingProxyType(dict(self.routing)))


class DeterministicClassifier(Protocol):
    def classify(
        self, request: str, registry: ProfileRegistry
    ) -> RouteCandidate | None: ...


class LocalRouter(Protocol):
    def route(
        self, request: str, catalog: Sequence[Mapping[str, object]]
    ) -> object | None: ...


@dataclass(frozen=True)
class KeywordRule:
    profile_id: str
    keywords: tuple[str, ...]
    confidence: float = 0.85
    reason: str = "keyword match"


class KeywordClassifier:
    """Small deterministic classifier that abstains on ties and no matches."""

    def __init__(self, rules: Iterable[KeywordRule], threshold: float = 0.7) -> None:
        self.rules = tuple(rules)
        self.threshold = threshold

    def classify(
        self, request: str, registry: ProfileRegistry
    ) -> RouteCandidate | None:
        text = request.casefold()
        matches: list[KeywordRule] = []
        for rule in self.rules:
            registry.get(rule.profile_id)
            if any(keyword.casefold() in text for keyword in rule.keywords):
                matches.append(rule)
        if not matches:
            return None
        matches.sort(key=lambda item: item.confidence, reverse=True)
        if len(matches) > 1 and matches[0].confidence == matches[1].confidence:
            return None
        winner = matches[0]
        if winner.confidence < self.threshold:
            return None
        return RouteCandidate(
            profile_id=winner.profile_id,
            confidence=winner.confidence,
            source="deterministic",
            reason=winner.reason,
        )


def parse_route_output(output: object, source: str = "local") -> RouteCandidate:
    """Parse JSON or FunctionGemma-style route output without executing it."""
    if isinstance(output, RouteCandidate):
        return output if output.source == source else RouteCandidate(
            profile_id=output.profile_id,
            confidence=output.confidence,
            source=source,
            reason=output.reason,
            required_capabilities=output.required_capabilities,
        )
    value: object = output
    if isinstance(output, str):
        text = output.strip()
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            match = re.fullmatch(
                r"<start_function_call>call:route_task\{(.*?)\}<end_function_call>",
                text,
                re.DOTALL,
            )
            if not match:
                raise RoutingError("local router output is not a route_task call")
            pairs = dict(re.findall(r"(profile|confidence):\s*([^,}]+)", match.group(1)))
            value = pairs
    if not isinstance(value, Mapping):
        raise RoutingError("route output must be an object")
    profile_id = value.get("profile", value.get("profile_id"))
    confidence = value.get("confidence")
    if not isinstance(profile_id, str) or not profile_id:
        raise RoutingError("route output must contain a profile")
    if confidence is None:
        raise RoutingError("route output must contain numeric confidence")
    try:
        score = float(str(confidence))
    except (TypeError, ValueError) as exc:
        raise RoutingError("route output must contain numeric confidence") from exc
    required = value.get("required_capabilities", ())
    if isinstance(required, str) or not isinstance(required, Sequence):
        raise RoutingError("required_capabilities must be a list")
    return RouteCandidate(
        profile_id=profile_id,
        confidence=score,
        source=source,
        reason=str(value.get("reason", "")),
        required_capabilities=frozenset(str(item) for item in required),
    )


class FunctionGemmaRouter:
    """Optional adapter around an injected FunctionGemma-compatible generator."""

    def __init__(self, generator: Callable[[str, Sequence[Mapping[str, object]]], object]):
        self._generator = generator

    def route(
        self, request: str, catalog: Sequence[Mapping[str, object]]
    ) -> RouteCandidate:
        return parse_route_output(self._generator(request, catalog), source="local")


class RoutingCoordinator:
    """Apply routing precedence and policy without executing specialist tools."""

    def __init__(
        self,
        registry: ProfileRegistry,
        *,
        deterministic: DeterministicClassifier | None = None,
        local_router: LocalRouter | None = None,
        escalation: Callable[[str, Sequence[Mapping[str, object]]], object | None]
        | None = None,
        threshold: float = 0.7,
        audit_sink: Callable[[Mapping[str, object]], None] | None = None,
    ) -> None:
        self.registry = registry
        self.deterministic = deterministic
        self.local_router = local_router
        self.escalation = escalation
        self.threshold = threshold
        self.audit_sink = audit_sink

    def _validate(
        self,
        candidate: RouteCandidate,
        *,
        required_capabilities: frozenset[str],
        requires_mutation: bool,
        explicit: bool,
        high_risk_approved: bool,
    ) -> SpecialistProfile:
        profile = self.registry.get(candidate.profile_id)
        needed = required_capabilities | candidate.required_capabilities
        missing = needed - profile.capabilities
        if missing:
            raise PolicyError(
                f"profile {profile.id!r} lacks capabilities: {sorted(missing)}"
            )
        if requires_mutation and not profile.allow_mutation:
            raise PolicyError(f"profile {profile.id!r} does not allow mutation")
        if profile.high_risk and not (explicit and high_risk_approved):
            raise PolicyError(f"high-risk profile {profile.id!r} requires explicit approval")
        return profile

    def _selected(
        self,
        candidate: RouteCandidate,
        profile: SpecialistProfile,
        *,
        candidates: list[str],
        escalated: bool = False,
    ) -> RouteDecision:
        decision = RouteDecision(
            status="selected",
            source=candidate.source,
            profile_id=profile.id,
            confidence=candidate.confidence,
            reason=candidate.reason,
            candidates=tuple(candidates),
            escalated=escalated,
        )
        self._audit(decision)
        return decision

    def _audit(self, decision: RouteDecision) -> None:
        if self.audit_sink is not None:
            self.audit_sink(
                {
                    "status": decision.status,
                    "source": decision.source,
                    "profile_id": decision.profile_id,
                    "confidence": decision.confidence,
                    "candidates": decision.candidates,
                    "escalated": decision.escalated,
                }
            )

    def route(
        self,
        request: str,
        *,
        explicit_profile: str | None = None,
        required_capabilities: Iterable[str] = (),
        requires_mutation: bool = False,
        high_risk_approved: bool = False,
    ) -> RouteDecision:
        required = frozenset(required_capabilities)
        candidates: list[str] = []
        if explicit_profile is not None:
            candidate = RouteCandidate(explicit_profile, 1.0, "explicit")
            profile = self._validate(
                candidate,
                required_capabilities=required,
                requires_mutation=requires_mutation,
                explicit=True,
                high_risk_approved=high_risk_approved,
            )
            return self._selected(candidate, profile, candidates=[profile.id])

        if self.deterministic is not None:
            candidate = self.deterministic.classify(request, self.registry)
            if candidate is not None:
                candidates.append(candidate.profile_id)
                if candidate.confidence >= self.threshold:
                    profile = self._validate(
                        candidate,
                        required_capabilities=required,
                        requires_mutation=requires_mutation,
                        explicit=False,
                        high_risk_approved=False,
                    )
                    return self._selected(candidate, profile, candidates=candidates)

        catalog = self.registry.catalog()
        if self.local_router is not None:
            try:
                candidate = parse_route_output(
                    self.local_router.route(request, catalog), source="local"
                )
                candidates.append(candidate.profile_id)
                if candidate.confidence >= self.threshold:
                    profile = self._validate(
                        candidate,
                        required_capabilities=required,
                        requires_mutation=requires_mutation,
                        explicit=False,
                        high_risk_approved=False,
                    )
                    return self._selected(candidate, profile, candidates=candidates)
            except (RoutingError, TypeError, ValueError):
                pass

        if self.escalation is not None:
            try:
                candidate = parse_route_output(
                    self.escalation(request, catalog), source="escalation"
                )
                candidates.append(candidate.profile_id)
                if candidate.confidence >= self.threshold:
                    profile = self._validate(
                        candidate,
                        required_capabilities=required,
                        requires_mutation=requires_mutation,
                        explicit=False,
                        high_risk_approved=False,
                    )
                    return self._selected(
                        candidate, profile, candidates=candidates, escalated=True
                    )
            except (RoutingError, TypeError, ValueError):
                pass

        decision = RouteDecision(
            status="unresolved",
            source="unresolved",
            reason="no permitted route met the confidence threshold",
            candidates=tuple(candidates),
            escalated=self.escalation is not None,
        )
        self._audit(decision)
        return decision

    def handoff(
        self,
        request: str,
        decision: RouteDecision,
        *,
        state: Mapping[str, Any] | None = None,
        constraints: Iterable[str] = (),
    ) -> SpecialistHandoff:
        if not decision.selected:
            raise RoutingError("cannot create a handoff for an unresolved route")
        profile = self.registry.get(decision.profile_id or "")
        return SpecialistHandoff(
            user_request=request,
            profile_id=profile.id,
            tools=profile.tools,
            state={} if state is None else state,
            constraints=tuple(constraints),
            routing={
                "source": decision.source,
                "confidence": decision.confidence,
                "reason": decision.reason,
            },
        )
