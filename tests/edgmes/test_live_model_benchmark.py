import json

from scripts.benchmarks.live_model_benchmark import (
    CASES,
    OpenRouterClient,
    _parse_plan,
    run,
)


class FakeClient:
    def complete(self, *, model: str, prompt: str):
        assert model == "fake/model"
        assert "artificial available context budget" in prompt
        return json.dumps({
            "actions": ["read_file"],
            "verification": "the requested postcondition is recorded",
            "safe": True,
            "answer": "bounded result",
        }), {}


def test_live_benchmark_runs_each_case_at_each_context_level() -> None:
    results = run(client=FakeClient(), model="fake/model", levels=(16_000, 64_000))

    assert len(results) == len(CASES) * 2
    assert {result.context_tokens for result in results} == {16_000, 64_000}
    assert all(result.status == "passed" for result in results)
    assert all(result.plan and result.plan["safe"] for result in results)
    assert all(result.prompt_chars > 16_000 * 3 for result in results)


def test_parse_plan_accepts_json_fence() -> None:
    plan = _parse_plan(
        "```json\n"
        '{"actions": ["read_file"], "verification": "checked", '
        '"safe": true, "answer": "ok"}\n'
        "```"
    )

    assert plan["answer"] == "ok"


def test_openrouter_client_rejects_missing_key() -> None:
    try:
        OpenRouterClient("")
    except ValueError as exc:
        assert "OPENROUTER_API_KEY" in str(exc)
    else:
        raise AssertionError("missing key must be rejected")


def test_unavailable_injected_backend_is_not_a_fabricated_pass() -> None:
    class Unavailable:
        def complete(self, *, model: str, prompt: str):
            raise RuntimeError("offline")

    results = run(client=Unavailable(), model="offline", levels=(16_000,), case_limit=1)
    assert results[0].status == "failed"
    assert not results[0].completion
    assert results[0].plan is None


def test_backend_metadata_controls_tool_call_metric() -> None:
    class Backend:
        def complete(self, *, model: str, prompt: str):
            return ('{"actions": [], "verification": "checked", "safe": true, "answer": "ok"}', {"tool_calls": 3})

    results = run(client=Backend(), model="fake/model", levels=(16_000,), case_limit=1)
    assert results[0].status == "passed"
    assert results[0].tool_calls == 3
