from __future__ import annotations

from pydantic import BaseModel, Field

from bear.domain.enums import PermissionLevel, RiskLevel


class ToolDefinition(BaseModel):
    name: str
    description: str
    argument_schema: dict[str, object]
    expected_side_effects: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    idempotent: bool
    required_permissions: list[PermissionLevel] = Field(default_factory=list)
    audit_logging_fields: list[str] = Field(default_factory=list)


class ToolRegistry(BaseModel):
    tools: dict[str, ToolDefinition] = Field(default_factory=dict)

    def register(self, definition: ToolDefinition) -> None:
        self.tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition:
        return self.tools[name]

    def list(self) -> list[ToolDefinition]:
        return list(self.tools.values())


def build_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name='read',
            description='Read local files and experiment artifacts.',
            argument_schema={'path': 'string'},
            expected_side_effects=[],
            risk_level=RiskLevel.LOW,
            idempotent=True,
            required_permissions=[PermissionLevel.ALLOW],
            audit_logging_fields=['path', 'project_id'],
        )
    )
    registry.register(
        ToolDefinition(
            name='edit',
            description='Modify local repository files for an experiment.',
            argument_schema={'path': 'string', 'patch': 'string'},
            expected_side_effects=['changes files'],
            risk_level=RiskLevel.MEDIUM,
            idempotent=False,
            required_permissions=[PermissionLevel.REQUEST],
            audit_logging_fields=['path', 'project_id', 'session_id'],
        )
    )
    registry.register(
        ToolDefinition(
            name='submit_slurm_job',
            description='Submit a cluster experiment to Slurm.',
            argument_schema={'script': 'string', 'resources': 'object'},
            expected_side_effects=['consumes cluster resources', 'creates scheduler job'],
            risk_level=RiskLevel.HIGH,
            idempotent=False,
            required_permissions=[PermissionLevel.REQUEST],
            audit_logging_fields=['project_id', 'plan_id', 'resource_request'],
        )
    )
    registry.register(
        ToolDefinition(
            name='run_experiment',
            description='Launch or submit an experiment execution through a backend.',
            argument_schema={'plan_id': 'string', 'dry_run': 'boolean'},
            expected_side_effects=['creates execution record', 'may consume compute resources'],
            risk_level=RiskLevel.MEDIUM,
            idempotent=False,
            required_permissions=[PermissionLevel.ALLOW, PermissionLevel.REQUEST],
            audit_logging_fields=['plan_id', 'dry_run', 'project_id'],
        )
    )
    registry.register(
        ToolDefinition(
            name='notify_human',
            description='Send approval or status information through a configured channel.',
            argument_schema={'channel': 'string', 'message': 'string'},
            expected_side_effects=['sends notification'],
            risk_level=RiskLevel.LOW,
            idempotent=False,
            required_permissions=[PermissionLevel.ALLOW],
            audit_logging_fields=['channel', 'project_id'],
        )
    )
    return registry
