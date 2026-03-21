# `policies2`

Execute stored policies and flows over REST using API keys only.

This SDK is intentionally narrow:

- execute policies
- execute flows
- authenticate with `x-api-key`

It does not support creating, updating, publishing, or administering resources.

## Usage

```python
from policies2 import ExecutionClient, ExecutionClientConfig, Reference, TransportConfig

client = ExecutionClient(
    ExecutionClientConfig(
        api_key="pk_live_example",
        transport=TransportConfig(base_url="https://api.policy2.net"),
    )
)

result = client.execute_policy(
    policy_id="3b7d4b2a-9aa0-4b6d-a1b4-9dcf11ce12ab",
    reference=Reference.BASE,
    data={"user": {"age": 25}},
)

print(result.result)
```

## Install

```bash
pip install policies2
```

Or, if you prefer requirements files:

```bash
pip install -r requirements-dev.txt
```

## Examples

- REST policy execution: [`examples/policy_rest.py`](./examples/policy_rest.py)
- REST flow execution: [`examples/flow_rest.py`](./examples/flow_rest.py)
