from pathlib import Path

from fastapi.testclient import TestClient

from bear.config.settings import Settings
from bear.runtime.service import build_service
from bear.web.app import create_app


def test_api_vertical_slice(tmp_path: Path) -> None:
    service = build_service(Settings(state_root=tmp_path / 'state'))
    client = TestClient(create_app(service))

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
    service = build_service(Settings(state_root=tmp_path / 'state'))
    client = TestClient(create_app(service))

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
