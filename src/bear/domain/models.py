from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from bear.domain.enums import (
    ApprovalStatus,
    ExecutionBackendKind,
    ExperimentStatus,
    PermissionLevel,
    RiskLevel,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f'{prefix}_{uuid4().hex[:12]}'


class BearModel(BaseModel):
    model_config = {'extra': 'forbid', 'use_enum_values': True}


class ResourceBudget(BearModel):
    max_concurrent_experiments: int = 1
    max_gpus: int = 0
    max_cpus: int = 4
    max_memory_gb: int = 16
    max_walltime_minutes: int = 60
    max_token_budget: int = 100_000
    max_model_cost_usd: float = 25.0
    retry_limit: int = 1
    cooldown_minutes: int = 10


class Project(BearModel):
    id: str = Field(default_factory=lambda: new_id('proj'))
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)
    local_path: str | None = None
    budget: ResourceBudget = Field(default_factory=ResourceBudget)
    created_at: datetime = Field(default_factory=utcnow)


class ResearchIdea(BearModel):
    id: str = Field(default_factory=lambda: new_id('idea'))
    project_id: str
    title: str
    problem_statement: str
    motivation: str
    created_at: datetime = Field(default_factory=utcnow)


class Hypothesis(BearModel):
    id: str = Field(default_factory=lambda: new_id('hyp'))
    project_id: str
    idea_id: str
    statement: str
    rationale: str
    success_signal: str
    created_at: datetime = Field(default_factory=utcnow)


class CodeTask(BearModel):
    id: str = Field(default_factory=lambda: new_id('task'))
    project_id: str
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)


class BackendTarget(BearModel):
    name: str
    kind: ExecutionBackendKind
    supports_gpu: bool = False
    supports_dry_run: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentPlan(BearModel):
    id: str = Field(default_factory=lambda: new_id('plan'))
    project_id: str
    hypothesis_id: str
    title: str
    objective: str
    code_tasks: list[CodeTask] = Field(default_factory=list)
    target: BackendTarget
    dry_run: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class Artifact(BearModel):
    id: str = Field(default_factory=lambda: new_id('artifact'))
    project_id: str
    execution_id: str
    path: str
    kind: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BearModel):
    id: str = Field(default_factory=lambda: new_id('toolcall'))
    tool_name: str
    permission: PermissionLevel
    risk_level: RiskLevel
    arguments: dict[str, Any] = Field(default_factory=dict)
    side_effect_summary: str
    audit_fields: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)


class ApprovalRequest(BearModel):
    id: str = Field(default_factory=lambda: new_id('approval'))
    action: str
    resource_id: str
    justification: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)


class ExperimentExecution(BearModel):
    id: str = Field(default_factory=lambda: new_id('run'))
    project_id: str
    plan_id: str
    target: BackendTarget
    status: ExperimentStatus = ExperimentStatus.PLANNED
    command: str
    dry_run: bool = True
    logs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class ResultSummary(BearModel):
    id: str = Field(default_factory=lambda: new_id('result'))
    project_id: str
    execution_id: str
    outcome: str
    metrics: dict[str, float] = Field(default_factory=dict)
    analysis: str
    suggested_next_step: str
    created_at: datetime = Field(default_factory=utcnow)


class Insight(BearModel):
    id: str = Field(default_factory=lambda: new_id('insight'))
    project_id: str | None = None
    title: str
    detail: str
    evidence: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class AgentSession(BearModel):
    id: str = Field(default_factory=lambda: new_id('session'))
    project_id: str | None = None
    mode: str
    objective: str
    status: str = 'running'
    created_at: datetime = Field(default_factory=utcnow)


class Conversation(BearModel):
    id: str = Field(default_factory=lambda: new_id('conversation'))
    project_id: str | None = None
    channel: str
    title: str
    created_at: datetime = Field(default_factory=utcnow)


class ChannelMessage(BearModel):
    id: str = Field(default_factory=lambda: new_id('message'))
    channel: str
    direction: str
    body: str
    created_at: datetime = Field(default_factory=utcnow)


class KnowledgeNode(BearModel):
    id: str = Field(default_factory=lambda: new_id('knowledge'))
    title: str
    summary: str
    project_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)


class CrossProjectLink(BearModel):
    id: str = Field(default_factory=lambda: new_id('link'))
    source_node_id: str
    target_node_id: str
    relationship: str
    rationale: str
