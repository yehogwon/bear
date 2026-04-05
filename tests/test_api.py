from pathlib import Path

from fastapi.testclient import TestClient

from bear.config.settings import Settings
from bear.runtime.service import build_service
from bear.web.app import create_app


def build_client(tmp_path: Path) -> TestClient:
    service = build_service(Settings(state_root=tmp_path / 'state'))
    return TestClient(create_app(service))


def test_api_vertical_slice(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    project = client.post(
        '/api/projects',
        json={'name': 'Project A', 'description': 'desc', 'tags': ['demo']},
    ).json()
    idea = client.post(
        f'/api/projects/{project["id"]}/ideas',
        json={'title': 'Idea', 'problem_statement': 'Problem', 'motivation': 'Why'},
    ).json()
    hypothesis = client.post(
        f'/api/projects/{project["id"]}/hypotheses',
        json={
            'idea_id': idea['id'],
            'statement': 'Hypothesis',
            'rationale': 'Because',
            'success_signal': 'Signal',
        },
    ).json()
    plan = client.post(
        f'/api/projects/{project["id"]}/plans',
        json={'hypothesis_id': hypothesis['id'], 'title': 'Plan', 'objective': 'Validate flow'},
    ).json()
    run = client.post(f'/api/plans/{plan["id"]}/run', json={'dry_run': True}).json()
    state = client.get('/api/state').json()
    knowledge = client.get('/api/knowledge').json()
    artifacts = client.get('/api/artifacts').json()
    session = client.post(
        '/api/sessions',
        json={'mode': 'autopilot', 'objective': 'Advance the project', 'project_id': project['id']},
    ).json()
    paused = client.post(f'/api/sessions/{session["id"]}/pause').json()

    assert run['execution']['plan_id'] == plan['id']
    assert run['result']['execution_id'] == run['execution']['id']
    assert len(state['projects']) == 1
    assert len(state['results']) == 1
    assert len(artifacts) == 1
    assert len(knowledge['nodes']) >= 3
    assert paused['status'] == 'paused'


def test_api_requires_approval_for_non_dry_run(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    project = client.post(
        '/api/projects',
        json={'name': 'Project B', 'description': 'desc', 'tags': ['demo']},
    ).json()
    idea = client.post(
        f'/api/projects/{project["id"]}/ideas',
        json={'title': 'Idea', 'problem_statement': 'Problem', 'motivation': 'Why'},
    ).json()
    hypothesis = client.post(
        f'/api/projects/{project["id"]}/hypotheses',
        json={
            'idea_id': idea['id'],
            'statement': 'Hypothesis',
            'rationale': 'Because',
            'success_signal': 'Signal',
        },
    ).json()
    plan = client.post(
        f'/api/projects/{project["id"]}/plans',
        json={'hypothesis_id': hypothesis['id'], 'title': 'Plan', 'objective': 'Validate flow'},
    ).json()

    approval_response = client.post(
        f'/api/plans/{plan["id"]}/request-execution',
        json={'dry_run': False},
    ).json()
    approved = client.post(f'/api/approvals/{approval_response["approval"]["id"]}/approve').json()
    run = client.post(f'/api/plans/{plan["id"]}/run', json={'dry_run': False}).json()

    assert approval_response['allowed'] is False
    assert approved['status'] == 'approved'
    assert run['execution']['status'] == 'running'


def test_index_route_returns_control_plane_html(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    response = client.get('/')

    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type']
    assert 'bear control plane' in response.text
    assert 'GET /api/knowledge' in response.text
    assert 'POST /api/knowledge/links' in response.text
    assert 'GET /api/tool-calls' in response.text


def test_api_approvals_and_tool_calls_routes_return_lists(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    approvals_response = client.get('/api/approvals')
    tool_calls_response = client.get('/api/tool-calls')

    assert approvals_response.status_code == 200
    assert approvals_response.json() == []
    assert tool_calls_response.status_code == 200
    assert tool_calls_response.json() == []


def test_api_can_create_knowledge_links(tmp_path: Path) -> None:
    client = build_client(tmp_path)

    project_a = client.post(
        '/api/projects',
        json={'name': 'Project A', 'description': 'desc', 'tags': ['demo']},
    ).json()
    idea_a = client.post(
        f'/api/projects/{project_a["id"]}/ideas',
        json={'title': 'Idea A', 'problem_statement': 'Problem', 'motivation': 'Why'},
    ).json()
    project_b = client.post(
        '/api/projects',
        json={'name': 'Project B', 'description': 'desc', 'tags': ['demo']},
    ).json()
    idea_b = client.post(
        f'/api/projects/{project_b["id"]}/ideas',
        json={'title': 'Idea B', 'problem_statement': 'Problem', 'motivation': 'Why'},
    ).json()

    before = client.get('/api/knowledge').json()
    response = client.post(
        '/api/knowledge/links',
        json={
            'source_node_id': idea_a['id'],
            'target_node_id': idea_b['id'],
            'relationship': 'supports',
            'rationale': 'The ideas share evidence.',
        },
    )
    after = client.get('/api/knowledge').json()

    assert response.status_code == 200
    assert response.json()['source_node_id'] == idea_a['id']
    assert response.json()['target_node_id'] == idea_b['id']
    assert response.json()['relationship'] == 'supports'
    assert len(before['links']) == 0
    assert after['links'] == [response.json()]



def test_api_exposes_execution_lifecycle_routes(tmp_path: Path) -> None:
    service = build_service(
        Settings(
            state_root=tmp_path / 'state',
            artifact_root=tmp_path / 'artifacts',
            execution_backend='local_cuda',
        )
    )
    client = TestClient(create_app(service))

    project = client.post(
        '/api/projects',
        json={'name': 'Project C', 'description': 'desc', 'tags': ['demo']},
    ).json()
    idea = client.post(
        f'/api/projects/{project["id"]}/ideas',
        json={'title': 'Idea', 'problem_statement': 'Problem', 'motivation': 'Why'},
    ).json()
    hypothesis = client.post(
        f'/api/projects/{project["id"]}/hypotheses',
        json={
            'idea_id': idea['id'],
            'statement': 'Hypothesis',
            'rationale': 'Because',
            'success_signal': 'Signal',
        },
    ).json()
    plan = client.post(
        f'/api/projects/{project["id"]}/plans',
        json={'hypothesis_id': hypothesis['id'], 'title': 'Plan', 'objective': 'Validate flow'},
    ).json()
    approval = client.post(
        f'/api/plans/{plan["id"]}/request-execution',
        json={'dry_run': False},
    ).json()
    _ = client.post(f'/api/approvals/{approval["approval"]["id"]}/approve').json()
    run = client.post(f'/api/plans/{plan["id"]}/run', json={'dry_run': False}).json()
    execution_id = run['execution']['id']

    fetched = client.get(f'/api/executions/{execution_id}').json()
    polled = client.post(f'/api/executions/{execution_id}/poll').json()
    logs = client.get(f'/api/executions/{execution_id}/logs').json()
    cancelled = client.post(f'/api/executions/{execution_id}/cancel').json()

    assert fetched['id'] == execution_id
    assert fetched['target']['kind'] == 'local_cuda'
    assert polled['execution']['id'] == execution_id
    assert logs['logs'][-1] == 'execution submitted'
    assert cancelled['execution']['status'] == 'cancelled'
