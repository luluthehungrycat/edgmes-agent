from dataclasses import FrozenInstanceError

import pytest

from edgmes.capabilities import (
    CapabilityProfileError,
    CapabilityProfileRegistry,
    ModelCapabilityProfile,
    PolicyRequest,
    UnknownCapabilityProfileError,
    resolve_tool_context_policy,
    default_capability_registry,
)


def profile(**overrides: object) -> ModelCapabilityProfile:
    values: dict[str, object] = {
        "id": "qwen-4b-edge",
        "description": "Small local model for bounded coding tasks",
        "context_budget": 16_000,
        "output_budget": 2_000,
        "capabilities": frozenset({"filesystem", "testing"}),
        "permitted_tools": frozenset({"read_file", "run_tests"}),
        "max_steps": 4,
        "max_tool_calls": 8,
    }
    values.update(overrides)
    return ModelCapabilityProfile(**values)


def test_valid_request_returns_bounded_allowed_policy() -> None:
    result = resolve_tool_context_policy(
        profile(),
        PolicyRequest(
            required_capabilities=frozenset({"filesystem"}),
            required_tools=frozenset({"read_file"}),
            optional_tools=frozenset({"run_tests", "write_file"}),
            estimated_context=16_000,
            requested_output=2_000,
            requested_steps=3,
            requested_tool_calls=5,
        ),
    )

    assert result.allowed
    assert result.permitted_tools == ("read_file", "run_tests")
    assert result.filtered_optional_tools == ("write_file",)
    assert result.max_steps == 3
    assert result.max_tool_calls == 5


def test_required_tool_or_capability_rejects_and_exposes_no_tools() -> None:
    result = resolve_tool_context_policy(
        profile(),
        PolicyRequest(
            required_capabilities=frozenset({"network"}),
            required_tools=frozenset({"write_file"}),
        ),
    )

    assert not result.allowed
    assert result.permitted_tools == ()
    assert "capability:network" in result.reasons
    assert "required_tool:write_file" in result.reasons


def test_optional_tools_are_filtered_without_rejection() -> None:
    result = resolve_tool_context_policy(
        profile(), PolicyRequest(optional_tools=frozenset({"write_file"}))
    )

    assert result.allowed
    assert result.permitted_tools == ()
    assert result.filtered_optional_tools == ("write_file",)


@pytest.mark.parametrize(
    "field, value",
    [("estimated_context", 16_001), ("requested_output", 2_001), ("requested_steps", 5), ("requested_tool_calls", 9)],
)
def test_budget_overflow_is_rejected(field: str, value: int) -> None:
    request = PolicyRequest(**{field: value})
    result = resolve_tool_context_policy(profile(), request)
    assert not result.allowed
    assert any(field in reason for reason in result.reasons)


def test_read_only_request_needs_no_mutation_approval() -> None:
    result = resolve_tool_context_policy(profile(), PolicyRequest())
    assert result.allowed


def test_mutation_requires_profile_permission_and_explicit_approval() -> None:
    request = PolicyRequest(requires_mutation=True, mutation_approved=True)
    assert not resolve_tool_context_policy(profile(), request).allowed
    assert resolve_tool_context_policy(
        profile(allow_mutation=True), request
    ).allowed
    assert not resolve_tool_context_policy(
        profile(allow_mutation=True), PolicyRequest(requires_mutation=True)
    ).allowed


def test_profile_is_immutable_and_rejects_secret_metadata() -> None:
    value = profile()
    with pytest.raises(FrozenInstanceError):
        value.context_budget = 1  # type: ignore[misc]

    with pytest.raises(CapabilityProfileError):
        profile(metadata={"api_key": "[REDACTED]"})


def test_registry_is_a_snapshot_and_unknown_profiles_fail_closed() -> None:
    registry = CapabilityProfileRegistry([profile()])
    assert registry.get("qwen-4b-edge").id == "qwen-4b-edge"
    assert registry.catalog()[0]["permitted_tools"] == ("read_file", "run_tests")
    with pytest.raises(UnknownCapabilityProfileError):
        registry.get("unknown")


def test_default_registry_contains_named_edge_presets() -> None:
    registry = default_capability_registry()

    assert {profile.id for profile in registry} == {"nano", "small", "medium-edge", "full", "edge-small"}
    assert registry.get("full").allow_mutation is True
    assert registry.get("nano").permitted_tools == frozenset()
