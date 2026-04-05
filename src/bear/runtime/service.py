from __future__ import annotations

from dataclasses import dataclass

from bear.backends.local import LocalExecutionBackend
from bear.config.settings import Settings
from bear.core.interfaces import CodingAgentBackend, LLMBackend
from bear.domain.enums import ApprovalStatus, PermissionLevel, RiskLevel
from bear.domain.models import (
    AgentSession,
    ApprovalRequest,
    Artifact,
    CodeTask,
    CrossProjectLink,
    ExperimentExecution,
    ExperimentPlan,
    Hypothesis,
    Insight,
    KnowledgeNode,
    Project,
    ResearchIdea,
    ResultSummary,
    ToolCall,
)
from bear.policy.permissions import PermissionPolicy
from bear.providers.factory import build_coding_agent_backend, build_llm_backend
from bear.storage.markdown import MarkdownRepository
from bear.tools.registry import ToolRegistry, build_default_registry

JsonDict = dict[str, object]


@dataclass(slots=True)
class BearService:
    repository: MarkdownRepository
    tool_registry: ToolRegistry
    permission_policy: PermissionPolicy
    execution_backend: LocalExecutionBackend
    llm_backend: LLMBackend
    coding_agent_backend: CodingAgentBackend

    def create_project(self, name: str, description: str, tags: list[str] | None = None) -> Project:
        project = Project(name=name, description=description, tags=tags or [])
        self.repository.save('projects', project.id, project.model_dump(mode='json'))
        knowledge = KnowledgeNode(
            title=project.name,
            summary=project.description,
            project_ids=[project.id],
            tags=['project', *project.tags],
        )
        self.repository.save('knowledge_nodes', knowledge.id, knowledge.model_dump(mode='json'))
        return project

    def create_idea(
        self, project_id: str, title: str, problem_statement: str, motivation: str
    ) -> ResearchIdea:
        idea = ResearchIdea(
            project_id=project_id,
            title=title,
            problem_statement=problem_statement,
            motivation=motivation,
        )
        self.repository.save('ideas', idea.id, idea.model_dump(mode='json'))
        return idea

    def create_hypothesis(
        self, project_id: str, idea_id: str, statement: str, rationale: str, success_signal: str
    ) -> Hypothesis:
        hypothesis = Hypothesis(
            project_id=project_id,
            idea_id=idea_id,
            statement=statement,
            rationale=rationale,
            success_signal=success_signal,
        )
        self.repository.save('hypotheses', hypothesis.id, hypothesis.model_dump(mode='json'))
        knowledge = KnowledgeNode(
            title=hypothesis.statement,
            summary=hypothesis.rationale,
            project_ids=[project_id],
            tags=['hypothesis'],
        )
        self.repository.save('knowledge_nodes', knowledge.id, knowledge.model_dump(mode='json'))
        return hypothesis

    def plan_experiment(
        self, project_id: str, hypothesis_id: str, title: str, objective: str
    ) -> ExperimentPlan:
        planning_brief = self.llm_backend.generate_text(
            self._build_planning_prompt(title=title, objective=objective)
        )
        patch_plan = self.coding_agent_backend.create_patch_plan(
            self._build_patch_objective(title=title, objective=objective)
        )
        code_task = CodeTask(
            project_id=project_id,
            title='Create experiment scaffold',
            description=(
                'Add the smallest code change necessary to validate the hypothesis.\n\n'
                f'LLM planning brief ({self.llm_backend.provider_name}): {planning_brief}\n\n'
                f'Coding agent patch plan ({self.coding_agent_backend.provider_name}): '
                f'{patch_plan}'
            ),
            acceptance_criteria=[
                'The experiment can be launched in dry-run mode.',
                'A measurable success signal is captured in the result summary.',
                'Provider planning guidance is preserved in the task description.',
            ],
        )
        plan = ExperimentPlan(
            project_id=project_id,
            hypothesis_id=hypothesis_id,
            title=title,
            objective=objective,
            code_tasks=[code_task],
            target=self.execution_backend.target,
            dry_run=True,
        )
        self.repository.save('plans', plan.id, plan.model_dump(mode='json'))
        planning_note = KnowledgeNode(
            title=f'{title} planning brief',
            summary=(
                f'{planning_brief}\n\nPatch plan source: {self.coding_agent_backend.provider_name}'
            ),
            project_ids=[project_id],
            tags=[
                'plan',
                'provider-guidance',
                self.llm_backend.provider_name,
                self.coding_agent_backend.provider_name,
            ],
        )
        self.repository.save(
            'knowledge_nodes', planning_note.id, planning_note.model_dump(mode='json')
        )
        return plan

    def request_plan_execution(self, plan_id: str, dry_run: bool = False) -> ApprovalRequest | None:
        plan_payload = self.repository.get('plans', plan_id)
        if plan_payload is None:
            raise KeyError(f'Unknown plan: {plan_id}')
        context = 'dry_run' if dry_run else None
        tool_call = self.audit_tool(
            'run_experiment',
            side_effect_summary='Requested experiment execution.',
            arguments={'plan_id': plan_id, 'dry_run': dry_run},
            context=context,
        )
        if tool_call.permission == PermissionLevel.ALLOW:
            return None
        if tool_call.permission == PermissionLevel.DISALLOW:
            raise PermissionError(f'Plan {plan_id} cannot be executed under the active policy.')
        approval = ApprovalRequest(
            action='run_experiment',
            resource_id=plan_id,
            justification='Execution requires explicit approval under the active policy.',
        )
        self.repository.save('approvals', approval.id, approval.model_dump(mode='json'))
        return approval

    def approve_request(self, approval_id: str) -> ApprovalRequest:
        payload = self.repository.get('approvals', approval_id)
        if payload is None:
            raise KeyError(f'Unknown approval: {approval_id}')
        approval = ApprovalRequest.model_validate(payload)
        approval.status = ApprovalStatus.APPROVED
        self.repository.save('approvals', approval.id, approval.model_dump(mode='json'))
        return approval

    def run_plan(
        self, plan_id: str, dry_run: bool = True
    ) -> tuple[ExperimentExecution, ResultSummary]:
        plan_payload = self.repository.get('plans', plan_id)
        if plan_payload is None:
            raise KeyError(f'Unknown plan: {plan_id}')
        plan = ExperimentPlan.model_validate(plan_payload)
        context = 'dry_run' if dry_run else None
        tool_call = self.audit_tool(
            'run_experiment',
            side_effect_summary='Executed experiment plan.',
            arguments={'plan_id': plan_id, 'dry_run': dry_run},
            context=context,
        )
        if tool_call.permission == PermissionLevel.DISALLOW:
            raise PermissionError(f'Plan {plan_id} cannot be executed under the active policy.')
        if tool_call.permission != PermissionLevel.ALLOW and not self._has_approved_request(
            plan_id
        ):
            raise PermissionError(f'Plan {plan_id} requires approval before execution.')
        execution = self.execution_backend.submit(plan, dry_run=dry_run)
        self.repository.save('executions', execution.id, execution.model_dump(mode='json'))
        artifacts = self._persist_artifacts(execution)
        analysis = self.llm_backend.generate_text(
            self._build_result_prompt(
                plan=plan, execution=execution, artifacts=artifacts, dry_run=dry_run
            )
        )
        next_step = self.coding_agent_backend.create_patch_plan(
            self._build_next_step_objective(plan=plan, dry_run=dry_run)
        )
        result = ResultSummary(
            project_id=plan.project_id,
            execution_id=execution.id,
            outcome='dry-run completed successfully'
            if dry_run
            else 'execution submitted successfully',
            metrics={'confidence': 0.6, 'latency_seconds': 0.1 if dry_run else 0.0},
            analysis=analysis,
            suggested_next_step=next_step,
        )
        self.repository.save('results', result.id, result.model_dump(mode='json'))
        insight = Insight(
            project_id=plan.project_id,
            title='Dry-run execution completed',
            detail=result.analysis,
            evidence=[execution.id, result.id],
        )
        self.repository.save('insights', insight.id, insight.model_dump(mode='json'))
        knowledge = KnowledgeNode(
            title=plan.title,
            summary=result.analysis,
            project_ids=[plan.project_id],
            tags=[
                'result',
                'dry-run' if dry_run else 'execution',
                self.llm_backend.provider_name,
                self.coding_agent_backend.provider_name,
                *[artifact.kind for artifact in artifacts],
            ],
        )
        self.repository.save('knowledge_nodes', knowledge.id, knowledge.model_dump(mode='json'))
        return execution, result

    def create_cross_project_link(
        self, source_node_id: str, target_node_id: str, relationship: str, rationale: str
    ) -> CrossProjectLink:
        link = CrossProjectLink(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship=relationship,
            rationale=rationale,
        )
        self.repository.save('cross_project_links', link.id, link.model_dump(mode='json'))
        return link

    def start_agent_session(
        self, mode: str, objective: str, project_id: str | None = None
    ) -> AgentSession:
        session = AgentSession(project_id=project_id, mode=mode, objective=objective)
        self.repository.save('agent_sessions', session.id, session.model_dump(mode='json'))
        return session

    def pause_agent_session(self, session_id: str) -> AgentSession:
        payload = self.repository.get('agent_sessions', session_id)
        if payload is None:
            raise KeyError(f'Unknown session: {session_id}')
        session = AgentSession.model_validate(payload)
        session.status = 'paused'
        self.repository.save('agent_sessions', session.id, session.model_dump(mode='json'))
        return session

    def snapshot(self) -> dict[str, list[JsonDict]]:
        namespaces = [
            'projects',
            'ideas',
            'hypotheses',
            'plans',
            'executions',
            'results',
            'insights',
            'artifacts',
            'knowledge_nodes',
            'cross_project_links',
            'approvals',
            'tool_calls',
            'agent_sessions',
        ]
        return {namespace: self.repository.list(namespace) for namespace in namespaces}

    def list_knowledge_nodes(self) -> list[KnowledgeNode]:
        payloads = self.repository.list('knowledge_nodes')
        return [KnowledgeNode.model_validate(payload) for payload in payloads]

    def list_cross_project_links(self) -> list[CrossProjectLink]:
        payloads = self.repository.list('cross_project_links')
        return [CrossProjectLink.model_validate(payload) for payload in payloads]

    def list_artifacts(self) -> list[Artifact]:
        payloads = self.repository.list('artifacts')
        return [Artifact.model_validate(payload) for payload in payloads]

    def list_pending_approvals(self) -> list[ApprovalRequest]:
        payloads = self.repository.list('approvals')
        return [
            ApprovalRequest.model_validate(payload)
            for payload in payloads
            if payload.get('status') == 'pending'
        ]

    def list_tool_calls(self) -> list[ToolCall]:
        payloads = self.repository.list('tool_calls')
        return [ToolCall.model_validate(payload) for payload in payloads]

    def audit_tool(
        self,
        tool_name: str,
        side_effect_summary: str,
        arguments: dict[str, object],
        context: str | None = None,
    ) -> ToolCall:
        decision = self.permission_policy.resolve(tool_name, context=context)
        tool_call = ToolCall(
            tool_name=tool_name,
            permission=decision.level,
            risk_level=RiskLevel.LOW
            if decision.level == PermissionLevel.ALLOW
            else RiskLevel.MEDIUM,
            arguments=arguments,
            side_effect_summary=side_effect_summary,
            audit_fields={'decision_reason': decision.reason},
        )
        self.repository.save('tool_calls', tool_call.id, tool_call.model_dump(mode='json'))
        return tool_call

    def _has_approved_request(self, plan_id: str) -> bool:
        return any(
            approval.action == 'run_experiment'
            and approval.resource_id == plan_id
            and approval.status == 'approved'
            for approval in self._list_approved_requests()
        )

    def _list_approved_requests(self) -> list[ApprovalRequest]:
        payloads = self.repository.list('approvals')
        return [
            ApprovalRequest.model_validate(payload)
            for payload in payloads
            if payload.get('status') == 'approved'
        ]

    def _persist_artifacts(self, execution: ExperimentExecution) -> list[Artifact]:
        artifacts: list[Artifact] = []
        for artifact_payload in self.execution_backend.fetch_artifacts(execution):
            path = artifact_payload.get('path')
            kind = artifact_payload.get('kind')
            if not isinstance(path, str) or not isinstance(kind, str):
                continue
            artifacts.append(
                Artifact(
                    project_id=execution.project_id,
                    execution_id=execution.id,
                    path=path,
                    kind=kind,
                    metadata={'target': execution.target.name},
                )
            )
        for artifact in artifacts:
            self.repository.save('artifacts', artifact.id, artifact.model_dump(mode='json'))
        return artifacts

    def _build_planning_prompt(self, *, title: str, objective: str) -> str:
        return '\n'.join(
            [
                'Summarize the smallest experiment plan that can validate the objective.',
                f'Plan title: {title}',
                f'Objective: {objective}',
                'Return plain text that names the success signal, a key risk, '
                'and the next verification step.',
            ]
        )

    def _build_patch_objective(self, *, title: str, objective: str) -> str:
        return '\n'.join(
            [
                f'Plan title: {title}',
                f'Objective: {objective}',
                'Generate a minimal patch plan that makes the experiment runnable '
                'in dry-run mode and keeps provider wiring covered by tests.',
            ]
        )

    def _build_result_prompt(
        self,
        *,
        plan: ExperimentPlan,
        execution: ExperimentExecution,
        artifacts: list[Artifact],
        dry_run: bool,
    ) -> str:
        artifact_paths = ', '.join(artifact.path for artifact in artifacts) or 'none'
        return '\n'.join(
            [
                'Summarize the execution result in plain text.',
                f'Plan title: {plan.title}',
                f'Objective: {plan.objective}',
                f'Execution status: {execution.status}',
                f'Dry run: {dry_run}',
                f'Artifacts: {artifact_paths}',
                'Include the current evidence and the most important follow-up concern.',
            ]
        )

    def _build_next_step_objective(self, *, plan: ExperimentPlan, dry_run: bool) -> str:
        if dry_run:
            return '\n'.join(
                [
                    f'Objective: promote the dry-run plan "{plan.title}" toward real execution.',
                    'Outline the smallest implementation and verification steps needed next.',
                ]
            )
        return '\n'.join(
            [
                f'Objective: follow up on the submitted execution for "{plan.title}".',
                'Outline the smallest steps to collect logs, inspect artifacts, '
                'and decide on the next patch.',
            ]
        )


def build_service(
    settings: Settings | None = None,
    *,
    llm_backend: LLMBackend | None = None,
    coding_agent_backend: CodingAgentBackend | None = None,
) -> BearService:
    settings = settings or Settings()
    repository = MarkdownRepository(settings.state_root)
    return BearService(
        repository=repository,
        tool_registry=build_default_registry(),
        permission_policy=PermissionPolicy(
            defaults=settings.default_permissions,
            context_overrides=settings.context_permissions,
        ),
        execution_backend=LocalExecutionBackend(),
        llm_backend=llm_backend or build_llm_backend(settings),
        coding_agent_backend=coding_agent_backend or build_coding_agent_backend(settings),
    )
