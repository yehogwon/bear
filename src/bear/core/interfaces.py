from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from bear.domain.models import (
    AgentSession,
    ApprovalRequest,
    ChannelMessage,
    ExperimentExecution,
    ExperimentPlan,
    Project,
    ResearchIdea,
    ResultSummary,
    ToolCall,
)

JsonDict = dict[str, object]


class Repository(Protocol):
    def save(self, namespace: str, model_id: str, payload: JsonDict) -> None: ...

    def get(self, namespace: str, model_id: str) -> JsonDict | None: ...

    def list(self, namespace: str) -> list[JsonDict]: ...


class ExecutionBackend(Protocol):
    def capability_summary(self) -> dict[str, object]: ...

    def prepare_environment(self, plan: ExperimentPlan) -> dict[str, object]: ...

    def generate_command(self, plan: ExperimentPlan) -> str: ...

    def submit(self, plan: ExperimentPlan, dry_run: bool = True) -> ExperimentExecution: ...

    def poll_status(self, execution: ExperimentExecution) -> ExperimentExecution: ...

    def fetch_logs(self, execution: ExperimentExecution) -> list[str]: ...

    def fetch_artifacts(self, execution: ExperimentExecution) -> list[dict[str, object]]: ...

    def cancel(self, execution: ExperimentExecution) -> ExperimentExecution: ...


class LLMBackend(Protocol):
    provider_name: str

    def generate_text(self, prompt: str) -> str: ...


class CodingAgentBackend(Protocol):
    provider_name: str

    def create_patch_plan(self, objective: str) -> str: ...


class CommunicationChannel(Protocol):
    channel_name: str

    def send_message(self, message: str) -> ChannelMessage: ...


class Planner(Protocol):
    def create_plan(
        self, project: Project, idea: ResearchIdea, hypothesis_text: str
    ) -> ExperimentPlan: ...


class Analyzer(Protocol):
    def summarize(self, execution: ExperimentExecution) -> ResultSummary: ...


class AuditLog(Protocol):
    def record_tool_call(self, tool_call: ToolCall) -> None: ...

    def list_tool_calls(self) -> Sequence[ToolCall]: ...


class ApprovalStore(Protocol):
    def create(self, approval: ApprovalRequest) -> None: ...

    def list_pending(self) -> list[ApprovalRequest]: ...


class SessionStore(Protocol):
    def create(self, session: AgentSession) -> None: ...
