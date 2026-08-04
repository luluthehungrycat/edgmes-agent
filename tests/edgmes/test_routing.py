from typing import Any

import pytest

from edgmes.routing import (
    FunctionGemmaRouter,
    KeywordClassifier,
    KeywordRule,
    ProfileRegistry,
    RouteCandidate,
    RoutingCoordinator,
    SpecialistProfile,
    UnknownProfileError,
)


def profiles() -> ProfileRegistry:
    return ProfileRegistry(
        [
            SpecialistProfile(
                id="coder",
                description="Modify and test source code",
                capabilities=frozenset({"filesystem", "testing"}),
                tools=("read_file", "patch", "terminal"),
                model_policy="qwen-coder",
                max_steps=8,
                max_tool_calls=8,
                allow_mutation=True,
            ),
            SpecialistProfile(
                id="docs-writer",
                description="Write documentation",
                capabilities=frozenset({"documentation", "filesystem"}),
                tools=("read_file", "write_file"),
                model_policy="qwen-small",
                max_steps=5,
                max_tool_calls=5,
                allow_mutation=True,
            ),
        ]
    )


class StubRouter:
    def __init__(self, response: object):
        self.response = response
        self.seen_catalog: tuple[dict[str, object], ...] = ()

    def route(self, request: str, catalog: Any) -> object:
        self.seen_catalog = tuple(catalog)
        return self.response


def test_unknown_profile_is_rejected() -> None:
    with pytest.raises(UnknownProfileError):
        profiles().get("trader")


def test_deterministic_routing_bypasses_local_router() -> None:
    router = StubRouter({"profile": "docs-writer", "confidence": 1})
    coordinator = RoutingCoordinator(
        profiles(),
        deterministic=KeywordClassifier(
            [KeywordRule("coder", ("python", "test failure"))]
        ),
        local_router=router,
    )
    decision = coordinator.route("Fix the Python test failure")
    assert decision.profile_id == "coder"
    assert decision.source == "deterministic"
    assert router.seen_catalog == ()


def test_local_router_uses_compact_catalog_and_handoff_is_bounded() -> None:
    seen: list[object] = []

    def generate(request: str, catalog: Any) -> object:
        seen.append(catalog)
        return {"profile": "docs-writer", "confidence": 0.91, "reason": "docs"}

    coordinator = RoutingCoordinator(profiles(), local_router=FunctionGemmaRouter(generate))
    decision = coordinator.route("Please improve the README")
    handoff = coordinator.handoff(
        "Please improve the README",
        decision,
        state={"goal": "README", "unrelated_transcript": "not included"},
        constraints=("verify diff",),
    )
    assert decision.profile_id == "docs-writer"
    assert handoff.tools == ("read_file", "write_file")
    assert len(seen[0]) == 2
    assert all("tools" not in profile for profile in seen[0])
    assert "unrelated_transcript" not in handoff.state
    assert handoff.user_request == "Please improve the README"


def test_functiongemma_style_output_is_strictly_parsed() -> None:
    from edgmes.routing import parse_route_output

    candidate = parse_route_output(
        "<start_function_call>call:route_task{profile:coder,confidence:0.88}"
        "<end_function_call>"
    )
    assert candidate == RouteCandidate("coder", 0.88, "local")


def test_invalid_local_router_escalates() -> None:
    escalation_calls: list[str] = []

    def escalate(request: str, catalog: Any) -> object:
        escalation_calls.append(request)
        return {"profile": "coder", "confidence": 0.95}

    coordinator = RoutingCoordinator(
        profiles(),
        local_router=StubRouter("not a route"),
        escalation=escalate,
    )
    decision = coordinator.route("ambiguous task")
    assert decision.profile_id == "coder"
    assert decision.source == "escalation"
    assert decision.escalated is True
    assert escalation_calls == ["ambiguous task"]


def test_low_confidence_without_escalation_is_unresolved() -> None:
    coordinator = RoutingCoordinator(
        profiles(),
        local_router=StubRouter({"profile": "coder", "confidence": 0.2}),
    )
    decision = coordinator.route("unclear")
    assert decision.status == "unresolved"


def test_router_cannot_expand_capabilities_or_mutate_through_readonly_profile() -> None:
    coordinator = RoutingCoordinator(
        profiles(),
        local_router=StubRouter(
            {
                "profile": "docs-writer",
                "confidence": 0.99,
                "required_capabilities": ["shell"],
            }
        ),
    )
    decision = coordinator.route("do something", requires_mutation=True)
    assert decision.status == "rejected"
    assert "lacks capabilities" in decision.reason


def test_explicit_profile_can_be_mutating_when_allowed() -> None:
    decision = RoutingCoordinator(profiles()).route(
        "edit code", explicit_profile="coder", requires_mutation=True
    )
    assert decision.selected is True


def test_audit_events_contain_no_request_or_secret() -> None:
    events: list[dict[str, object]] = []
    coordinator = RoutingCoordinator(
        profiles(),
        local_router=StubRouter({"profile": "coder", "confidence": 0.9}),
        audit_sink=events.append,
    )
    coordinator.route("token=super-secret")
    assert events[0]["profile_id"] == "coder"
    assert "super-secret" not in repr(events[0])
