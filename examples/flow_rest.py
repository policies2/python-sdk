from policies2_sdk import ExecutionClient, ExecutionClientConfig, Reference, TransportConfig


client = ExecutionClient(
    ExecutionClientConfig(
        api_key="pk_live_example",
        transport=TransportConfig(base_url="https://api.policy2.net"),
    )
)

response = client.execute_flow(
    flow_id="ae6fb044-ad2b-45fd-82d1-0d2f1fa176a5",
    reference=Reference.BASE,
    data={
        "drivingTest": {
            "person": {
                "name": "Alice",
                "dateOfBirth": "1992-05-12",
            }
        }
    },
)

print("Flow result:", response.result)
print("Visited nodes:", len(response.node_response))
