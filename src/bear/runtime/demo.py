from __future__ import annotations

from bear.runtime.service import build_service


def main() -> None:
    service = build_service()
    project = service.create_project(
        name='Neural optimizer research',
        description='Explore small-scale optimizer interventions with auditable dry-run execution.',
        tags=['optimization', 'dry-run'],
    )
    idea = service.create_idea(
        project_id=project.id,
        title='Adaptive optimizer checkpointing',
        problem_statement='Training jobs restart too slowly after interruptions.',
        motivation='Faster recovery increases useful cluster throughput.',
    )
    hypothesis = service.create_hypothesis(
        project_id=project.id,
        idea_id=idea.id,
        statement='If checkpoint intervals adapt to loss volatility, restart waste will drop.',
        rationale='Higher volatility periods justify denser checkpoints.',
        success_signal='A dry-run plan captures a measurable recovery-latency metric.',
    )
    plan = service.plan_experiment(
        project_id=project.id,
        hypothesis_id=hypothesis.id,
        title='Checkpoint adaptation dry-run',
        objective='Validate the command, audit, and result flow before touching a live backend.',
    )
    execution, result = service.run_plan(plan.id)

    print(f'project={project.id} plan={plan.id} execution={execution.id}')
    print(result.outcome)
    print(result.suggested_next_step)


if __name__ == '__main__':
    main()
