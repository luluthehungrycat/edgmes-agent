"""Public Edgmes namespace exports."""

from .home import EdgmesHome, HomeConfigurationError
from .ledger import (
    ContextBudgetError,
    ContextProjection,
    LedgerEntry,
    LedgerError,
    StateLedger,
    select_bounded_context,
)
from .capabilities import (
    CapabilityProfileError,
    CapabilityProfileRegistry,
    ModelCapabilityProfile,
    PolicyDecision,
    PolicyRequest,
    UnknownCapabilityProfileError,
    resolve_tool_context_policy,
)

__version__ = "0.1.0.dev0"
from .routing import (
    FunctionGemmaRouter,
    KeywordClassifier,
    KeywordRule,
    PolicyError,
    ProfileRegistry,
    RouteCandidate,
    RouteDecision,
    RoutingCoordinator,
    RoutingError,
    SpecialistHandoff,
    SpecialistProfile,
    UnknownProfileError,
    parse_route_output,
)

__all__ = [
    "EdgmesHome",
    "BackendResponse",
    "BackendTransportError",
    "EdgeRuntime",
    "EdgeRuntimeError",
    "OllamaBackend",
    "RuntimePolicyError",
    "RuntimeRequest",
    "RuntimeResult",
    "default_edge_profile",
    "ContextBudgetError",
    "ContextProjection",
    "LedgerEntry",
    "LedgerError",
    "StateLedger",
    "select_bounded_context",
    "CapabilityProfileError",
    "CapabilityProfileRegistry",
    "ModelCapabilityProfile",
    "PolicyDecision",
    "PolicyRequest",
    "UnknownCapabilityProfileError",
    "resolve_tool_context_policy",
    "FunctionGemmaRouter",
    "HomeConfigurationError",
    "KeywordClassifier",
    "KeywordRule",
    "PolicyError",
    "ProfileRegistry",
    "RouteCandidate",
    "RouteDecision",
    "RoutingCoordinator",
    "RoutingError",
    "SpecialistHandoff",
    "SpecialistProfile",
    "UnknownProfileError",
    "parse_route_output",
]

_RUNTIME_EXPORTS = frozenset({
    "BackendResponse",
    "BackendTransportError",
    "EdgeRuntime",
    "EdgeRuntimeError",
    "OllamaBackend",
    "RuntimePolicyError",
    "RuntimeRequest",
    "RuntimeResult",
    "default_edge_profile",
})


def __getattr__(name: str):
    if name in _RUNTIME_EXPORTS:
        from . import runtime

        return getattr(runtime, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
