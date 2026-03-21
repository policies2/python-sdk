from __future__ import annotations

import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ServerError,
    TransportError,
)
from .types import (
    ExecuteFlowRequest,
    ExecutePolicyRequest,
    ExecutionClientConfig,
    ExecutionTiming,
    FlowExecutionResult,
    FlowExecutionTiming,
    FlowNodeExecution,
    FlowNodeResponse,
    OrchestratorTiming,
    PolicyExecutionData,
    PolicyExecutionResult,
    Reference,
)


class ExecutionClient:
    def __init__(
        self,
        config: ExecutionClientConfig,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if not config.api_key.strip():
            raise ConfigurationError("api_key is required")
        if not config.transport.base_url.strip():
            raise ConfigurationError("transport.base_url is required")

        self._api_key = config.api_key
        self._base_url = config.transport.base_url.rstrip("/")
        self._timeout = config.timeout
        self._user_agent = config.user_agent
        self._opener = opener

    def execute_policy(
        self,
        request: ExecutePolicyRequest | None = None,
        *,
        policy_id: str | None = None,
        data: dict[str, Any] | None = None,
        reference: Reference = Reference.VERSION,
    ) -> PolicyExecutionResult:
        req = request or ExecutePolicyRequest(id=policy_id or "", data=data or {}, reference=reference)
        payload = self._send(self._policy_path(req.id, req.reference), req.data)
        return self._parse_policy_result(payload, kind="policy")

    def execute_flow(
        self,
        request: ExecuteFlowRequest | None = None,
        *,
        flow_id: str | None = None,
        data: dict[str, Any] | None = None,
        reference: Reference = Reference.VERSION,
    ) -> FlowExecutionResult:
        req = request or ExecuteFlowRequest(id=flow_id or "", data=data or {}, reference=reference)
        payload = self._send(self._flow_path(req.id, req.reference), req.data)
        return self._parse_flow_result(payload, kind="flow")

    def _send(self, path: str, data: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps({"data": data}).encode("utf-8")
        headers = {
            "content-type": "application/json",
            "x-api-key": self._api_key,
        }
        if self._user_agent:
            headers["user-agent"] = self._user_agent

        request = Request(
            url=f"{self._base_url}{path}",
            data=body,
            headers=headers,
            method="POST",
        )

        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            try:
                payload = exc.read().decode("utf-8").strip()
            finally:
                exc.close()
            if exc.code == 401:
                raise AuthenticationError(payload or "request rejected: invalid API key") from exc
            if exc.code == 403:
                raise AuthorizationError(payload or "request rejected: insufficient permissions") from exc
            raise ServerError(payload or f"request failed with status {exc.code}", status=exc.code) from exc
        except URLError as exc:
            raise TransportError("REST execution request failed") from exc

        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise TransportError("failed to decode response body") from exc

    @staticmethod
    def _policy_path(identifier: str, reference: Reference) -> str:
        return f"/run/policy/{identifier}" if reference == Reference.BASE else f"/run/policy_version/{identifier}"

    @staticmethod
    def _flow_path(identifier: str, reference: Reference) -> str:
        return f"/run/flow/{identifier}" if reference == Reference.BASE else f"/run/flow_version/{identifier}"

    @staticmethod
    def _parse_execution_timing(value: Any) -> ExecutionTiming | None:
        if not isinstance(value, dict):
            return None
        orchestrator = value.get("orchestrator")
        parsed_orchestrator = None
        if isinstance(orchestrator, dict):
            parsed_orchestrator = OrchestratorTiming(
                go=str(orchestrator.get("go", "")),
                database=str(orchestrator.get("database", "")),
                total=str(orchestrator.get("total", "")),
            )
        return ExecutionTiming(
            orchestrator=parsed_orchestrator,
            engine=str(value.get("engine", "")),
            total=str(value.get("total", "")),
        )

    @staticmethod
    def _parse_flow_execution_timing(value: Any) -> FlowExecutionTiming | None:
        if not isinstance(value, dict):
            return None
        return FlowExecutionTiming(
            orchestrator=str(value.get("orchestrator", "")),
            database=str(value.get("database", "")),
            engine=str(value.get("engine", "")),
            total=str(value.get("total", "")),
        )

    def _parse_policy_result(self, payload: dict[str, Any], *, kind: str) -> PolicyExecutionResult:
        return PolicyExecutionResult(
            kind=kind,
            result=bool(payload.get("result", False)),
            trace=payload.get("trace"),
            rule=list(payload.get("rule", [])),
            data=payload.get("data"),
            error=payload.get("error", payload.get("errors")),
            labels=payload.get("labels"),
            execution=self._parse_execution_timing(payload.get("execution")),
            timings=self._parse_execution_timing(payload.get("timings")),
        )

    def _parse_flow_result(self, payload: dict[str, Any], *, kind: str) -> FlowExecutionResult:
        node_response = []
        for node in payload.get("nodeResponse", []):
            response = node.get("response", {})
            parsed_execution = node.get("execution")
            node_response.append(
                FlowNodeResponse(
                    node_id=str(node.get("nodeId", "")),
                    node_type=str(node.get("nodeType", "")),
                    response=PolicyExecutionData(
                        result=bool(response.get("result", False)),
                        trace=response.get("trace"),
                        rule=list(response.get("rule", [])),
                        data=response.get("data"),
                        error=response.get("error", response.get("errors")),
                        labels=response.get("labels"),
                    ),
                    execution=(
                        FlowNodeExecution(
                            database=str(parsed_execution.get("database", "")),
                            engine=str(parsed_execution.get("engine", "")),
                            total=str(parsed_execution.get("total", "")),
                        )
                        if isinstance(parsed_execution, dict)
                        else None
                    ),
                )
            )

        return FlowExecutionResult(
            kind=kind,
            result=payload.get("result"),
            node_response=node_response,
            execution=self._parse_flow_execution_timing(payload.get("execution")),
            timings=self._parse_flow_execution_timing(payload.get("timings")),
        )
