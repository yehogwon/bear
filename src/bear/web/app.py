from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from bear.config.settings import Settings
from bear.runtime.service import BearService, build_service

JsonDict = dict[str, object]


class ProjectCreateRequest(BaseModel):
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


class IdeaCreateRequest(BaseModel):
    title: str
    problem_statement: str
    motivation: str


class HypothesisCreateRequest(BaseModel):
    idea_id: str
    statement: str
    rationale: str
    success_signal: str


class PlanCreateRequest(BaseModel):
    hypothesis_id: str
    title: str
    objective: str


class ExecutionRequest(BaseModel):
    dry_run: bool = True


class AgentSessionCreateRequest(BaseModel):
    mode: str
    objective: str
    project_id: str | None = None


class KnowledgeLinkRequest(BaseModel):
    source_node_id: str
    target_node_id: str
    relationship: str
    rationale: str


def create_app(service: BearService | None = None) -> FastAPI:
    app = FastAPI(title='bear')
    active_service = service or build_service(Settings())

    @app.get('/', response_class=HTMLResponse)
    def index() -> str:
        return """
        <html>
          <head><title>bear control plane</title></head>
          <body>
            <h1>bear control plane</h1>
            <p>Create projects and inspect the current state through the JSON API.</p>
            <ul>
              <li>POST /api/projects</li>
              <li>POST /api/projects/{project_id}/ideas</li>
              <li>POST /api/projects/{project_id}/hypotheses</li>
              <li>POST /api/projects/{project_id}/plans</li>
              <li>POST /api/plans/{plan_id}/request-execution</li>
              <li>POST /api/plans/{plan_id}/run</li>
              <li>POST /api/sessions</li>
              <li>POST /api/sessions/{session_id}/pause</li>
              <li>GET /api/knowledge</li>
              <li>GET /api/state</li>
            </ul>
          </body>
        </html>
        """

    @app.get('/api/state')
    def state() -> dict[str, list[JsonDict]]:
        return active_service.snapshot()

    @app.post('/api/projects')
    def create_project(payload: ProjectCreateRequest) -> JsonDict:
        return active_service.create_project(
            payload.name, payload.description, payload.tags
        ).model_dump(mode='json')

    @app.post('/api/projects/{project_id}/ideas')
    def create_idea(project_id: str, payload: IdeaCreateRequest) -> JsonDict:
        return active_service.create_idea(
            project_id=project_id,
            title=payload.title,
            problem_statement=payload.problem_statement,
            motivation=payload.motivation,
        ).model_dump(mode='json')

    @app.post('/api/projects/{project_id}/hypotheses')
    def create_hypothesis(project_id: str, payload: HypothesisCreateRequest) -> JsonDict:
        return active_service.create_hypothesis(
            project_id=project_id,
            idea_id=payload.idea_id,
            statement=payload.statement,
            rationale=payload.rationale,
            success_signal=payload.success_signal,
        ).model_dump(mode='json')

    @app.post('/api/projects/{project_id}/plans')
    def create_plan(project_id: str, payload: PlanCreateRequest) -> JsonDict:
        return active_service.plan_experiment(
            project_id=project_id,
            hypothesis_id=payload.hypothesis_id,
            title=payload.title,
            objective=payload.objective,
        ).model_dump(mode='json')

    @app.post('/api/plans/{plan_id}/request-execution')
    def request_execution(plan_id: str, payload: ExecutionRequest) -> JsonDict:
        approval = active_service.request_plan_execution(plan_id, dry_run=payload.dry_run)
        if approval is None:
            return {'allowed': True, 'dry_run': payload.dry_run}
        return {'allowed': False, 'approval': approval.model_dump(mode='json')}

    @app.post('/api/plans/{plan_id}/run')
    def run_plan(plan_id: str, payload: ExecutionRequest) -> JsonDict:
        execution, result = active_service.run_plan(plan_id, dry_run=payload.dry_run)
        return {
            'execution': execution.model_dump(mode='json'),
            'result': result.model_dump(mode='json'),
        }

    @app.post('/api/approvals/{approval_id}/approve')
    def approve(approval_id: str) -> JsonDict:
        return active_service.approve_request(approval_id).model_dump(mode='json')

    @app.get('/api/approvals')
    def approvals() -> list[JsonDict]:
        return [
            approval.model_dump(mode='json') for approval in active_service.list_pending_approvals()
        ]

    @app.get('/api/knowledge')
    def knowledge() -> JsonDict:
        return {
            'nodes': [
                node.model_dump(mode='json') for node in active_service.list_knowledge_nodes()
            ],
            'links': [
                link.model_dump(mode='json') for link in active_service.list_cross_project_links()
            ],
        }

    @app.get('/api/artifacts')
    def artifacts() -> list[JsonDict]:
        return [artifact.model_dump(mode='json') for artifact in active_service.list_artifacts()]

    @app.post('/api/knowledge/links')
    def create_link(payload: KnowledgeLinkRequest) -> JsonDict:
        return active_service.create_cross_project_link(
            source_node_id=payload.source_node_id,
            target_node_id=payload.target_node_id,
            relationship=payload.relationship,
            rationale=payload.rationale,
        ).model_dump(mode='json')

    @app.post('/api/sessions')
    def start_session(payload: AgentSessionCreateRequest) -> JsonDict:
        return active_service.start_agent_session(
            mode=payload.mode,
            objective=payload.objective,
            project_id=payload.project_id,
        ).model_dump(mode='json')

    @app.post('/api/sessions/{session_id}/pause')
    def pause_session(session_id: str) -> JsonDict:
        return active_service.pause_agent_session(session_id).model_dump(mode='json')

    @app.get('/api/tool-calls')
    def tool_calls() -> list[JsonDict]:
        return [tool_call.model_dump(mode='json') for tool_call in active_service.list_tool_calls()]

    return app
