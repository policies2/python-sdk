from policies2_sdk import ExecutionClient, ExecutionClientConfig, Reference, TransportConfig


client = ExecutionClient(
    ExecutionClientConfig(
        api_key="pk_live_example",
        transport=TransportConfig(base_url="https://api.policy2.net"),
    )
)

response = client.execute_policy(
    policy_id="3b7d4b2a-9aa0-4b6d-a1b4-9dcf11ce12ab",
    reference=Reference.BASE,
    data={
        "drivingTest": {
            "person": {
                "name": "Bob",
                "dateOfBirth": "1990-01-01",
            }
        }
    },
)

print("Policy result:", response.result)
