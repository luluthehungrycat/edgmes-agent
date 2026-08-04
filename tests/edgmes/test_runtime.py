import json

import pytest

from edgmes.capabilities import ModelCapabilityProfile
from edgmes.ledger import LedgerEntry, StateLedger
from edgmes.runtime import (
    BackendResponse,
    EdgeRuntime,
    RuntimeRequest,
    RuntimePolicyError,
    default_edge_profile,
)


class FakeBackend:
    def __init__(self, text: str = "local answer") -> None:
        self.text = text
        self.calls: list[tuple[list[dict[str, str]], str, int]] = []

    def complete(self, messages, *, model: str, max_output: int) -> BackendResponse:
        self.calls.append((messages, model, max_output))
        return BackendResponse(self.text, {"backend": "fake", "model": model})


def test_runtime_projects_ledger_and_records_verified_result() -> None:
    backend = FakeBackend()
    runtime = EdgeRuntime(
        backend=backend,
        model="small-local",
        profile=default_edge_profile(context_budget=512, output_budget=64),
        ledger=StateLedger((LedgerEntry("fact", "durable_fact", "The cat is black", verified=True),)),
    )

    result = runtime.run(RuntimeRequest(prompt="Describe the known fact."))

    assert result.text == "local answer"
    assert result.policy.allowed
    assert result.selected_context == ("request-2", "fact")
    assert result.ledger.entries[-1].category == "verification"
    assert backend.calls[0][1:] == ("small-local", 64)
    assert "The cat is black" in json.dumps(backend.calls[0][0])


def test_runtime_rejects_before_backend_when_output_exceeds_profile() -> None:
    backend = FakeBackend()
    runtime = EdgeRuntime(
        backend=backend,
        model="small-local",
        profile=ModelCapabilityProfile("edge", "test", 128, 8),
    )

    with pytest.raises(RuntimePolicyError):
        runtime.run(RuntimeRequest(prompt="answer", requested_output=9))
    assert backend.calls == []


def test_runtime_does_not_send_raw_transcript() -> None:
    backend = FakeBackend()
    runtime = EdgeRuntime(
        backend=backend,
        model="small-local",
        profile=default_edge_profile(context_budget=256, output_budget=32),
        ledger=StateLedger((LedgerEntry("goal", "current_goal", "Inspect the file"),)),
    )

    runtime.run(RuntimeRequest(prompt="Continue."))
    payload = json.dumps(backend.calls[0][0])
    assert "role" in payload
    assert "raw transcript" not in payload


def test_default_profile_is_single_step_and_has_no_tools() -> None:
    profile = default_edge_profile()
    assert profile.max_steps == 1
    assert profile.permitted_tools == frozenset()
    assert profile.allow_mutation is False
