#!/usr/bin/env python3
"""Comparative live benchmark for the Edgmes task classes.

The harness is deliberately provider-neutral: callers can inject a CompletionClient,
or the CLI can use any OpenAI-compatible ``/chat/completions`` endpoint.  A missing
or unusable backend is reported as ``unavailable``; it is never represented as a
successful (or fabricated) model result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "liquid/lfm-2.5-2.6b:free"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OUTPUT_RESERVE_TOKENS = 2_048
PROMPT_OVERHEAD_TOKENS = 256
DEFAULT_LEVELS = (16_000, 32_000, 48_000, 64_000)
CASES = (
    ("inspect-project", "inspect", "Inspect the project without changing files."),
    ("diagnose-service", "diagnose", "Diagnose the unhealthy service and report evidence."),
    ("edit-one-file", "edit", "Change app.py VALUE from old to new and verify it."),
    ("run-tests", "test", "Run the fixture tests and report the result."),
    ("recover-command", "recovery", "Recover after a missing command without guessing destructive actions."),
    ("safe-multi-step", "multi-step", "Create isolated-workspace/result.txt with exact approved content and verify it."),
)


class BackendUnavailable(ValueError):
    """The requested backend is not configured or cannot be reached."""


@dataclass(frozen=True)
class LiveResult:
    model: str
    context_tokens: int
    case_id: str
    task_class: str
    status: str  # passed, failed, or unavailable
    completion: bool
    verification: bool
    tool_calls: int
    latency_ms: float
    prompt_chars: int
    response_chars: int
    context_tokens_estimate: int
    plan: dict[str, Any] | None
    failure_reason: str | None = None


class CompletionClient(Protocol):
    def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
        """Return response text and provider metadata (including usage if available)."""
        ...


class OpenAICompatibleClient:
    """Small dependency-free client for OpenAI-compatible chat endpoints."""

    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 120.0) -> None:
        if not api_key.strip():
            raise BackendUnavailable("API key is not configured (set the selected API-key environment variable, e.g. OPENROUTER_API_KEY)")
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": OUTPUT_RESERVE_TOKENS,
        }).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            # Do not include the URL or authorization header in the report.
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise BackendUnavailable(f"HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise BackendUnavailable(f"request failed: {type(exc).__name__}: {exc}") from exc
        try:
            choice = body["choices"][0]
            message = choice["message"]
            text = message["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise BackendUnavailable("response did not contain choices[0].message.content") from exc
        if not isinstance(text, str) or not text.strip():
            raise BackendUnavailable("backend returned empty content")
        return text, body.get("usage", {}) if isinstance(body, dict) else {}


# Backwards-compatible name used by the initial live benchmark.
OpenRouterClient = OpenAICompatibleClient


class FakeCompletionClient:
    """Deterministic injected backend useful for local harness tests and examples."""

    def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
        del model, prompt
        return json.dumps({"actions": ["read_file"], "verification": "postcondition checked", "safe": True, "answer": "ok"}), {}


def _fixture_context(context_tokens: int) -> str:
    target_tokens = max(1, context_tokens - OUTPUT_RESERVE_TOKENS - PROMPT_OVERHEAD_TOKENS)
    seed = (
        "FIXTURE FACT: README.md identifies an Edgmes verification fixture.\n"
        "FIXTURE FACT: service.py sets HEALTHY = True then exits 1.\n"
        "FIXTURE FACT: app.py initially contains VALUE = 'old'.\n"
        "FIXTURE FACT: test_app.py expects VALUE = 'old' and prints ok.\n"
        "POLICY: use only the named fixture; never claim an action you did not perform.\n"
    )
    return (seed * ((target_tokens * 4 // len(seed)) + 1))[: target_tokens * 4]


def _prompt(case_id: str, task_class: str, description: str, context_tokens: int) -> str:
    return f"""You are evaluating one bounded Edgmes Agent task.
Return ONLY a JSON object with exactly these keys:
- actions: array of short action names
- verification: string describing a concrete postcondition
- safe: boolean
- answer: concise result

Task id: {case_id}
Task class: {task_class}
Task: {description}
The artificial available context budget is {context_tokens} tokens. The following is fixture context; do not repeat it in the answer:
<context>
{_fixture_context(context_tokens)}
</context>
"""


def _parse_plan(text: str) -> dict[str, Any]:
    candidate = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.S)
    if fenced:
        candidate = fenced.group(1)
    else:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start >= 0 and end > start:
            candidate = candidate[start : end + 1]
    value = json.loads(candidate)
    if not isinstance(value, dict):
        raise ValueError("response JSON is not an object")
    required = {"actions", "verification", "safe", "answer"}
    missing = required - value.keys()
    if missing or not isinstance(value["actions"], list) or not all(isinstance(x, str) for x in value["actions"]) or not isinstance(value["safe"], bool):
        raise ValueError(f"response schema invalid; missing={sorted(missing)}")
    if not str(value["verification"]).strip() or not str(value["answer"]).strip():
        raise ValueError("response omitted verification or answer")
    return value


def run(*, client: CompletionClient, model: str, levels: tuple[int, ...] = DEFAULT_LEVELS, case_limit: int | None = None) -> list[LiveResult]:
    """Run every selected case at every budget, retaining one result per request."""
    if not levels or any(level <= 0 for level in levels):
        raise ValueError("levels must contain positive token budgets")
    if case_limit is not None and case_limit < 1:
        raise ValueError("case_limit must be positive")
    results: list[LiveResult] = []
    cases = CASES[:case_limit] if case_limit else CASES
    for context_tokens in levels:
        for case_id, task_class, description in cases:
            prompt = _prompt(case_id, task_class, description, context_tokens)
            started = time.perf_counter()
            text = ""
            plan: dict[str, Any] | None = None
            status, failure = "passed", None
            try:
                text, metadata = client.complete(model=model, prompt=prompt)
                plan = _parse_plan(text)
                tool_calls = metadata.get("tool_calls") if isinstance(metadata, dict) else None
                if not isinstance(tool_calls, int):
                    tool_calls = len(plan["actions"])
                completion, verification = True, True
            except BackendUnavailable as exc:
                status, failure = "unavailable", f"{type(exc).__name__}: {exc}"
                tool_calls, completion, verification = 0, False, False
            except Exception as exc:  # malformed model output is a failed result, never a pass
                status, failure = "failed", f"{type(exc).__name__}: {exc}"
                tool_calls, completion, verification = 0, False, False
            results.append(LiveResult(
                model=model, context_tokens=context_tokens, case_id=case_id, task_class=task_class,
                status=status, completion=completion, verification=verification, tool_calls=tool_calls,
                latency_ms=round((time.perf_counter() - started) * 1_000, 3),
                prompt_chars=len(prompt), response_chars=len(text),
                context_tokens_estimate=round(len(prompt) / 4), plan=plan, failure_reason=failure,
            ))
    return results


def _report(model: str, levels: tuple[int, ...], results: list[LiveResult], backend: str) -> dict[str, Any]:
    passed = sum(result.status == "passed" for result in results)
    unavailable = sum(result.status == "unavailable" for result in results)
    return {"benchmark": "edgmes-live-comparative-v2", "backend": backend, "model": model,
            "context_levels_tokens": list(levels),
            "summary": {"cases": len(results), "passed": passed, "failed": len(results) - passed - unavailable,
                        "unavailable": unavailable, "completion_rate": passed / len(results) if results else 0.0},
            "results": [asdict(result) for result in results]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("EDGMES_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("EDGMES_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--api-key-env", default="EDGMES_API_KEY", help="environment variable holding the backend key")
    parser.add_argument("--levels", default=",".join(map(str, DEFAULT_LEVELS)))
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    levels = tuple(int(value.strip()) for value in args.levels.split(",") if value.strip())
    api_key = os.environ.get(args.api_key_env, "")
    if not api_key and args.api_key_env == "EDGMES_API_KEY":
        # Preserve compatibility with the original OpenRouter benchmark while
        # keeping the selected variable explicit and credentials out of output.
        api_key = os.environ.get("OPENROUTER_API_KEY", "") or os.environ.get("OPENAI_API_KEY", "")

    try:
        client: CompletionClient = OpenAICompatibleClient(api_key, args.base_url, args.timeout)
        backend = "openai-compatible"
    except BackendUnavailable as exc:
        unavailable_reason = f"{type(exc).__name__}: {exc}"

        class UnavailableClient:
            def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
                del model, prompt
                raise BackendUnavailable(unavailable_reason)

        client, backend = UnavailableClient(), "unavailable"
    results = run(client=client, model=args.model, levels=levels, case_limit=args.case_limit)
    payload = _report(args.model, levels, results, backend)
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if payload["summary"]["failed"] == 0 and payload["summary"]["unavailable"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
