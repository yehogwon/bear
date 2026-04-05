from pathlib import Path

from bear.config.settings import Settings
from bear.domain.enums import PermissionLevel
from bear.runtime.service import build_service


def test_vertical_slice_persists_entities(tmp_path: Path) -> None:
    service = build_service(Settings(state_root=tmp_path / 'state'))

    project = service.create_project('Project A', 'Research project')
    idea = service.create_idea(project.id, 'Idea', 'Problem', 'Motivation')
    hypothesis = service.create_hypothesis(project.id, idea.id, 'Statement', 'Rationale', 'Signal')
    plan = service.plan_experiment(project.id, hypothesis.id, 'Plan', 'Objective')
    execution, result = service.run_plan(plan.id)

    snapshot = service.snapshot()

    assert snapshot['projects'][0]['id'] == project.id
    assert snapshot['ideas'][0]['id'] == idea.id
    assert snapshot['hypotheses'][0]['id'] == hypothesis.id
    assert snapshot['plans'][0]['id'] == plan.id
    assert execution.plan_id == plan.id
    assert result.execution_id == execution.id
    assert len(snapshot['artifacts']) == 1
    assert len(snapshot['knowledge_nodes']) >= 3


def test_execution_approval_and_session_controls(tmp_path: Path) -> None:
    service = build_service(Settings(state_root=tmp_path / 'state'))

    project = service.create_project('Project A', 'Research project')
    idea = service.create_idea(project.id, 'Idea', 'Problem', 'Motivation')
    hypothesis = service.create_hypothesis(project.id, idea.id, 'Statement', 'Rationale', 'Signal')
    plan = service.plan_experiment(project.id, hypothesis.id, 'Plan', 'Objective')
    approval = service.request_plan_execution(plan.id, dry_run=False)
    session = service.start_agent_session('semi-autopilot', 'Monitor the project', project.id)

    assert approval is not None
    assert approval.resource_id == plan.id
    assert session.status == 'running'

    approved = service.approve_request(approval.id)
    paused = service.pause_agent_session(session.id)
    execution, result = service.run_plan(plan.id, dry_run=False)

    assert approved.status == 'approved'
    assert paused.status == 'paused'
    assert execution.status == 'running'
    assert execution.logs[-1] == 'execution submitted'
    assert result.outcome == 'execution submitted successfully'


def test_disallow_permission_blocks_request_and_execution(tmp_path: Path) -> None:
    settings = Settings(
        state_root=tmp_path / 'state',
        context_permissions={'dry_run': {'run_experiment': PermissionLevel.DISALLOW}},
    )
    service = build_service(settings)

    project = service.create_project('Project C', 'Research project')
    idea = service.create_idea(project.id, 'Idea', 'Problem', 'Motivation')
    hypothesis = service.create_hypothesis(project.id, idea.id, 'Statement', 'Rationale', 'Signal')
    plan = service.plan_experiment(project.id, hypothesis.id, 'Plan', 'Objective')

    try:
        service.request_plan_execution(plan.id, dry_run=True)
    except PermissionError:
        pass
    else:
        raise AssertionError('expected PermissionError for disallowed request')

    try:
        service.run_plan(plan.id, dry_run=True)
    except PermissionError:
        pass
    else:
        raise AssertionError('expected PermissionError for disallowed execution')
