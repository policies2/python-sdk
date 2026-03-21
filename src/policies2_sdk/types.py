from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Reference(str, Enum):
    BASE = "base"
    VERSION = "version"


@dataclass(slots=True)
class TransportConfig:
    base_url: str


@dataclass(slots=True)
class ExecutionClientConfig:
    api_key: str
    transport: TransportConfig
    timeout: float = 30.0
    user_agent: str | None = None


@dataclass(slots=True)
class ExecutePolicyRequest:
    id: str
    data: dict[str, Any]
    reference: Reference = Reference.VERSION


@dataclass(slots=True)
class ExecuteFlowRequest:
    id: str
    data: dict[str, Any]
    reference: Reference = Reference.VERSION


@dataclass(slots=True)
class OrchestratorTiming:
    go: str
    database: str
    total: str


@dataclass(slots=True)
class ExecutionTiming:
    orchestrator: OrchestratorTiming | None
    engine: str
    total: str


@dataclass(slots=True)
class PolicyExecutionData:
    result: bool
    trace: Any
    rule: list[str]
    data: Any
    error: Any
    labels: Any


@dataclass(slots=True)
class PolicyExecutionResult:
    kind: str
    result: bool
    trace: Any
    rule: list[str]
    data: Any
    error: Any
    labels: Any
    execution: ExecutionTiming | None = None
    timings: ExecutionTiming | None = None


@dataclass(slots=True)
class FlowNodeExecution:
    database: str
    engine: str
    total: str


@dataclass(slots=True)
class FlowNodeResponse:
    node_id: str
    node_type: str
    response: PolicyExecutionData
    execution: FlowNodeExecution | None = None


@dataclass(slots=True)
class FlowExecutionTiming:
    orchestrator: str
    database: str
    engine: str
    total: str


@dataclass(slots=True)
class FlowExecutionResult:
    kind: str
    result: Any
    node_response: list[FlowNodeResponse] = field(default_factory=list)
    execution: FlowExecutionTiming | None = None
    timings: FlowExecutionTiming | None = None
