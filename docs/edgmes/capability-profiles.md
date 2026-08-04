# Capability profiles and policy resolution

Edgmes separates *what a task needs* from *what the executing model can safely handle*.

A `ModelCapabilityProfile` is immutable metadata for one model tier. It declares:

- context and output budgets;
- supported capabilities such as `filesystem` or `testing`;
- permitted tool identifiers;
- maximum steps and tool calls;
- tool-calling and mutation policy.

`resolve_tool_context_policy(profile, request)` is a pure admission-control boundary. It does not call a model, inspect the filesystem, access credentials, or execute tools.

Policy behavior:

- required capabilities and tools are fail-closed;
- optional tools are filtered out when unavailable;
- context, output, step, and tool-call overflow is rejected;
- mutation requires both profile permission and explicit request approval;
- rejected decisions expose no executable tools;
- accepted decisions expose only the sorted bounded tool list.

Example:

```python
from edgmes import ModelCapabilityProfile, PolicyRequest, resolve_tool_context_policy

profile = ModelCapabilityProfile(
    id="qwen-4b-edge",
    description="Small local model",
    context_budget=16_000,
    output_budget=2_000,
    capabilities=frozenset({"filesystem", "testing"}),
    permitted_tools=frozenset({"read_file", "run_tests"}),
    max_steps=4,
    max_tool_calls=8,
)

decision = resolve_tool_context_policy(
    profile,
    PolicyRequest(
        required_capabilities=frozenset({"filesystem"}),
        required_tools=frozenset({"read_file"}),
        optional_tools=frozenset({"run_tests", "write_file"}),
        estimated_context=12_000,
    ),
)
```

The resolver returns an allowed decision with `read_file` and `run_tests`; `write_file` is filtered as optional and unavailable. The later edge runtime will use this contract before assembling a model request.
