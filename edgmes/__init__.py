"""Public Edgmes namespace exports."""

from .home import EdgmesHome, HomeConfigurationError
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
