#!/usr/bin/env python3
"""Run the Edgmes verification tasks against an OpenAI-compatible model.

This is a live planning benchmark, not an execution benchmark: the model sees
an isolated fixture description and must return a bounded JSON action plan. The
context levels are artificial prompt budgets used to measure behavior as the
available context grows from 16k to 64k tokens.
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


@dataclass(frozen=True)
class LiveResult:
    model: str
    context_tokens: int
    case_id: str
    task_class: str
    status: str
    latency_ms: float
    prompt_chars: int
    response_chars: int
    plan: dict[str, Any] | None
    failure_reason: str | None = None


class CompletionClient(Protocol):
    def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
        ...


class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: float = 120.0) -> None:
        if not api_key.strip():
            raise ValueError("OPENROUTER_API_KEY is not set")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(self, *, model: str, prompt: str) -> tuple[str, dict[str, Any]]:
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 2048,
            "reasoning": {"effort": "low"},
        }).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/luluthehungrycat/edgmes-agent",
                "X-Title": "Edgmes live verification benchmark",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"OpenRouter request failed: {type(exc).__name__}: {exc}") from exc
        try:
            choice = body["choices"][0]
            text = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"OpenRouter returned invalid response: {body!r}") from exc
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("OpenRouter returned empty content")
        return text, body


def _fixture_context(context_tokens: int) -> str:
    target_tokens = max(1, context_tokens - OUTPUT_RESERVE_TOKENS - PROMPT_OVERHEAD_TOKENS)
    target_chars = target_tokens * 4
    seed = (
        "FIXTURE FACT: README.md identifies an Edgmes verification fixture.\n"
        "FIXTURE FACT: service.py sets HEALTHY = True then exits 1.\n"
        "FIXTURE FACT: app.py initially contains VALUE = 'old'.\n"
        "FIXTURE FACT: test_app.py expects VALUE = 'old' and prints ok.\n"
        "POLICY: use only the named fixture; never claim an action you did not perform.\n"
    )
    repeats = (target_chars // len(seed)) + 1
    return (seed * repeats)[:target_chars]


def _prompt(case_id: str, task_class: str, description: str, context_tokens: int) -> str:
    context = _fixture_context(context_tokens)
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
{context}
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
    if missing or not isinstance(value["actions"], list) or not isinstance(value["safe"], bool):
        raise ValueError(f"response schema invalid; missing={sorted(missing)}")
    if not str(value["verification"]).strip() or not str(value["answer"]).strip():
        raise ValueError("response omitted verification or answer")
    return value


def run(*, client: CompletionClient, model: str, levels: tuple[int, ...], case_limit: int | None = None) -> list[LiveResult]:
    results: list[LiveResult] = []
    cases = CASES[:case_limit] if case_limit else CASES
    for context_tokens in levels:
        for case_id, task_class, description in cases:
            prompt = _prompt(case_id, task_class, description, context_tokens)
            started = time.perf_counter()
            try:
                text, _metadata = client.complete(model=model, prompt=prompt)
                plan = _parse_plan(text)
                status, failure = "passed", None
            except Exception as exc:
                text, plan = "", None
                status, failure = "failed", f"{type(exc).__name__}: {exc}"
            results.append(LiveResult(
                model=model,
                context_tokens=context_tokens,
                case_id=case_id,
                task_class=task_class,
                status=status,
                latency_ms=round((time.perf_counter() - started) * 1_000, 3),
                prompt_chars=len(prompt),
                response_chars=len(text),
                plan=plan,
                failure_reason=failure,
            ))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=os.environ.get("EDGMES_OPENROUTER_MODEL", DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL))
    parser.add_argument("--levels", default=",".join(map(str, DEFAULT_LEVELS)))
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    levels = tuple(int(value) for value in args.levels.split(",") if value.strip())
    client = OpenRouterClient(os.environ.get("OPENROUTER_API_KEY", ""), args.base_url)
    results = run(client=client, model=args.model, levels=levels, case_limit=args.case_limit)
    payload = {
        "benchmark": "edgmes-live-planning-v1",
        "model": args.model,
        "context_levels_tokens": levels,
        "summary": {
            "cases": len(results),
            "passed": sum(result.status == "passed" for result in results),
            "completion_rate": sum(result.status == "passed" for result in results) / len(results),
        },
        "results": [asdict(result) for result in results],
    }
    encoded = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if payload["summary"]["passed"] == payload["summary"]["cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
