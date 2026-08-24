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
