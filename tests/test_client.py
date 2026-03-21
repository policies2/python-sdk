from __future__ import annotations

import io
import json
import unittest
from urllib.error import HTTPError, URLError

from policies2 import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ExecutionClient,
    ExecutionClientConfig,
    Reference,
    ServerError,
    TransportConfig,
    TransportError,
)


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ExecutionClientTests(unittest.TestCase):
    def test_requires_api_key(self):
        with self.assertRaises(ConfigurationError):
            ExecutionClient(
                ExecutionClientConfig(api_key="", transport=TransportConfig(base_url="https://example.com"))
            )

    def test_execute_policy_uses_base_path_and_parses_result(self):
        captured = {}

        def opener(request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["api_key"] = request.headers["X-api-key"]
            body = json.loads(request.data.decode("utf-8"))
            captured["body"] = body
            return FakeResponse(
                {
                    "result": True,
                    "trace": {"execution": []},
                    "rule": ["A rule"],
                    "data": {"user": {"age": 25}},
                    "error": None,
                    "labels": None,
                    "execution": {
                        "orchestrator": {"go": "1", "database": "2", "total": "3"},
                        "engine": "4",
                        "total": "5",
                    },
                }
            )

        client = ExecutionClient(
            ExecutionClientConfig(
                api_key="test-key",
                transport=TransportConfig(base_url="https://api.policy2.net/"),
            ),
            opener=opener,
        )

        result = client.execute_policy(
            policy_id="policy-1",
            reference=Reference.BASE,
            data={"user": {"age": 25}},
        )

        self.assertEqual("https://api.policy2.net/run/policy/policy-1", captured["url"])
        self.assertEqual({"data": {"user": {"age": 25}}}, captured["body"])
        self.assertEqual("test-key", captured["api_key"])
        self.assertTrue(result.result)
        self.assertEqual("policy", result.kind)
        self.assertEqual("4", result.execution.engine)

    def test_execute_flow_uses_version_path_and_parses_nodes(self):
        def opener(request, timeout):
            return FakeResponse(
                {
                    "result": {"approved": True},
                    "nodeResponse": [
                        {
                            "nodeId": "node-1",
                            "nodeType": "policy",
                            "response": {
                                "result": True,
                                "trace": None,
                                "rule": ["A rule"],
                                "data": {"ok": True},
                                "error": None,
                                "labels": None,
                            },
                            "execution": {"database": "1", "engine": "2", "total": "3"},
                        }
                    ],
                    "execution": {"orchestrator": "1", "database": "2", "engine": "3", "total": "4"},
                }
            )

        client = ExecutionClient(
            ExecutionClientConfig(api_key="test-key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        result = client.execute_flow(flow_id="flow-1", data={"user": {"age": 25}})

        self.assertEqual("flow", result.kind)
        self.assertEqual(1, len(result.node_response))
        self.assertEqual("node-1", result.node_response[0].node_id)
        self.assertEqual("3", result.execution.engine)

    def test_maps_401_to_authentication_error(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 401, "Unauthorized", hdrs=None, fp=io.BytesIO(b"bad key"))

        client = ExecutionClient(
            ExecutionClientConfig(api_key="bad-key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        with self.assertRaises(AuthenticationError):
            client.execute_policy(policy_id="policy-1", data={})

    def test_maps_403_to_authorization_error(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 403, "Forbidden", hdrs=None, fp=io.BytesIO(b"forbidden"))

        client = ExecutionClient(
            ExecutionClientConfig(api_key="bad-key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        with self.assertRaises(AuthorizationError):
            client.execute_flow(flow_id="flow-1", data={})

    def test_maps_other_status_to_server_error(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 500, "Boom", hdrs=None, fp=io.BytesIO(b"server exploded"))

        client = ExecutionClient(
            ExecutionClientConfig(api_key="key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        with self.assertRaises(ServerError) as ctx:
            client.execute_policy(policy_id="policy-1", data={})

        self.assertEqual(500, ctx.exception.status)

    def test_maps_url_errors_to_transport_error(self):
        def opener(request, timeout):
            raise URLError("dns down")

        client = ExecutionClient(
            ExecutionClientConfig(api_key="key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        with self.assertRaises(TransportError):
            client.execute_policy(policy_id="policy-1", data={})

    def test_invalid_json_raises_transport_error(self):
        class BadResponse:
            def read(self) -> bytes:
                return b"{"

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def opener(request, timeout):
            return BadResponse()

        client = ExecutionClient(
            ExecutionClientConfig(api_key="key", transport=TransportConfig(base_url="https://api.policy2.net")),
            opener=opener,
        )

        with self.assertRaises(TransportError):
            client.execute_policy(policy_id="policy-1", data={})


if __name__ == "__main__":
    unittest.main()
