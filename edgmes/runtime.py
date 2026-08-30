"""Bounded, provider-neutral Edgmes runtime entry point."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .capabilities import (
    ModelCapabilityProfile,
    CapabilityProfileRegistry,
    PolicyDecision,
    PolicyRequest,
    UnknownCapabilityProfileError,
    default_capability_registry,
    resolve_tool_context_policy,
)
from .ledger import ContextBudgetError, StateLedger, LedgerEntry, Tokenizer, select_bounded_context


class EdgeRuntimeError(RuntimeError):
    """Base error for bounded runtime failures."""


class RuntimePolicyError(EdgeRuntimeError):
    """The request cannot be executed under the selected profile."""


class BackendTransportError(EdgeRuntimeError):
    """The injected backend did not return a valid response."""


@dataclass(frozen=True)
class BackendResponse:
    text: str
    evidence: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise BackendTransportError("backend returned an empty response")
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))


class ChatBackend(Protocol):
    def complete(
        self, messages: Sequence[Mapping[str, str]], *, model: str, max_output: int
    ) -> BackendResponse:
        """Complete one bounded chat request."""
        ...


@dataclass(frozen=True)
class RuntimeRequest:
    prompt: str
    requested_output: int = 0
    profile_id: str | None = None
    required_capabilities: frozenset[str] = frozenset()
    required_tools: frozenset[str] = frozenset()
    optional_tools: frozenset[str] = frozenset()
    requested_steps: int = 1
    requested_tool_calls: int = 0
    requires_mutation: bool = False
    mutation_approved: bool = False

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("runtime prompt must not be empty")
        if not isinstance(self.requested_output, int) or self.requested_output < 0:
            raise ValueError("requested_output must be a non-negative integer")
        if self.profile_id is not None and not self.profile_id.strip():
            raise ValueError("profile_id must not be empty")


@dataclass(frozen=True)
class RuntimeResult:
    text: str
    model: str
    profile_id: str
    policy: PolicyDecision
    selected_context: tuple[str, ...]
    evidence: Mapping[str, object]
    ledger: StateLedger
    measured_context: int = 0
    measurement_mode: str = "character-fallback"


class OllamaBackend:
    """Small non-streaming Ollama `/api/chat` adapter using only stdlib HTTP."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120.0) -> None:
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Ollama base_url must be an HTTP(S) URL with a hostname")
        if parsed.username or parsed.password:
            raise ValueError("Ollama base_url must not contain credentials")
        if timeout <= 0:
            raise ValueError("Ollama timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def complete(
        self, messages: Sequence[Mapping[str, str]], *, model: str, max_output: int
    ) -> BackendResponse:
        payload = json.dumps(
            {
                "model": model,
                "messages": list(messages),
                "stream": False,
                "options": {"num_predict": max_output},
            }
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise BackendTransportError(f"Ollama request failed: {type(exc).__name__}") from exc
        try:
            body = json.loads(raw.decode("utf-8"))
            text = body["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise BackendTransportError("Ollama returned invalid chat JSON") from exc
        if not isinstance(text, str) or not text.strip():
            raise BackendTransportError("Ollama returned no message content")
        return BackendResponse(
            text,
            {
                "backend": "ollama",
                "model": body.get("model", model),
                "done": body.get("done", False),
                "prompt_eval_count": body.get("prompt_eval_count", 0),
                "eval_count": body.get("eval_count", 0),
            },
        )


def default_edge_profile(*, context_budget: int = 12_000, output_budget: int = 512) -> ModelCapabilityProfile:
    """Return the conservative single-step profile used by the CLI."""

    return ModelCapabilityProfile(
        id="edge-small",
        description="Single-step local model with no executable tools",
        context_budget=context_budget,
        output_budget=output_budget,
        capabilities=frozenset({"chat"}),
        permitted_tools=frozenset(),
        max_steps=1,
        max_tool_calls=1,
        allow_mutation=False,
        supports_tool_calling=False,
    )


class EdgeRuntime:
    """Compose policy, bounded state selection, and one injected backend call."""

    _SYSTEM = "You are Edgmes Agent Edge. Answer the current request concisely and do not claim actions you did not perform."

    def __init__(
        self,
        *,
        backend: ChatBackend,
        model: str,
        profile: ModelCapabilityProfile | None = None,
        ledger: StateLedger | None = None,
        profiles: CapabilityProfileRegistry | None = None,
        default_profile_id: str | None = None,
        ledger_path: str | Path | None = None,
        tokenizer: Tokenizer | None = None,
    ) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        self.backend = backend
        self.model = model
        if profiles is None:
            if profile is not None:
                profiles = CapabilityProfileRegistry((profile,))
                default_profile_id = profile.id
            else:
                profiles = default_capability_registry()
                default_profile_id = default_profile_id or "edge-small"
        self.profiles = profiles
        self.default_profile_id = default_profile_id or "edge-small"
        try:
            self.profile = self.profiles.get(self.default_profile_id)
        except UnknownCapabilityProfileError as exc:
            raise ValueError(str(exc)) from exc
        self.ledger_path = Path(ledger_path) if ledger_path is not None else None
        self.tokenizer = tokenizer
        self.ledger = (
            StateLedger.load(self.ledger_path)
            if ledger is None and self.ledger_path is not None and self.ledger_path.exists()
            else ledger or StateLedger()
        )

    def _profile_for(self, request: RuntimeRequest) -> ModelCapabilityProfile:
        profile_id = request.profile_id or self.default_profile_id
        try:
            return self.profiles.get(profile_id)
        except UnknownCapabilityProfileError as exc:
            raise RuntimePolicyError(str(exc)) from exc

    def run(self, request: RuntimeRequest) -> RuntimeResult:
        profile = self._profile_for(request)
        turn_number = len(self.ledger.entries) + 1
        request_id = f"request-{turn_number}"
        current = LedgerEntry(request_id, "current_request", request.prompt, mandatory=True, recency=turn_number)
        try:
            projection = select_bounded_context(
                (*self.ledger.entries, current),
                budget=profile.context_budget,
                tokenizer=self.tokenizer,
                prefix=f"{self._SYSTEM}\n\n",
            )
        except ContextBudgetError as exc:
            raise RuntimePolicyError(str(exc)) from exc
        estimated_context = projection.measured_count
        policy = resolve_tool_context_policy(
            profile,
            PolicyRequest(
                required_capabilities=request.required_capabilities,
                required_tools=request.required_tools,
                optional_tools=request.optional_tools,
                estimated_context=estimated_context,
                requested_output=request.requested_output,
                requested_steps=request.requested_steps,
                requested_tool_calls=request.requested_tool_calls,
                requires_mutation=request.requires_mutation,
                mutation_approved=request.mutation_approved,
            ),
        )
        if not policy.allowed:
            raise RuntimePolicyError("; ".join(policy.reasons))
        selected_context = tuple(item.entry_id for item in projection.selected)
        content = projection.rendered_text
        response = self.backend.complete(
            (
                {"role": "system", "content": self._SYSTEM},
                {"role": "user", "content": content},
            ),
            model=self.model,
            max_output=policy.max_output,
        )
        updated = self.ledger.append(current)
        updated = updated.append(
            LedgerEntry(
                f"completed-{turn_number}",
                "completed_action",
                "One bounded local-model response returned",
            )
        )
        updated = updated.append(
            LedgerEntry(
                f"verification-{turn_number}",
                "verification",
                "Backend returned non-empty response content",
                verified=True,
            )
        )
        self.ledger = updated
        if self.ledger_path is not None:
            self.ledger.save(self.ledger_path)
        return RuntimeResult(
            response.text,
            self.model,
            profile.id,
            policy,
            selected_context,
            response.evidence,
            updated,
            projection.measured_count,
            projection.measurement_mode,
        )


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded Edgmes local-model turn")
    parser.add_argument("prompt")
    parser.add_argument("--model", default=os.environ.get("EDGMES_MODEL", "jaahas/qwen3.5-uncensored:2b"))
    parser.add_argument("--profile", default=os.environ.get("EDGMES_PROFILE", "edge-small"))
    parser.add_argument("--ledger-path", type=Path, default=os.environ.get("EDGMES_LEDGER_PATH"))
    parser.add_argument("--base-url", default=os.environ.get("EDGMES_OLLAMA_URL", "http://127.0.0.1:11434"))
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    result = EdgeRuntime(
        backend=OllamaBackend(args.base_url, args.timeout),
        model=args.model,
        default_profile_id=args.profile,
        ledger_path=args.ledger_path,
    ).run(RuntimeRequest(args.prompt))
    if args.as_json:
        print(json.dumps({
            "text": result.text,
            "model": result.model,
            "profile_id": result.profile_id,
            "selected_context": result.selected_context,
            "measured_context": result.measured_context,
            "measurement_mode": result.measurement_mode,
            "evidence": dict(result.evidence),
            "ledger_entries": len(result.ledger.entries),
        }, ensure_ascii=False))
    else:
        print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
