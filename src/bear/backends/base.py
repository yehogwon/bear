from __future__ import annotations

from pathlib import Path

from bear.domain.enums import ExperimentStatus
from bear.domain.models import BackendTarget, ExperimentExecution, ExperimentPlan


class BaseExecutionBackend:
    def __init__(self, target: BackendTarget, artifact_root: str | Path = '.bear/artifacts') -> None:
        self.target = target
        self.artifact_root = Path(artifact_root)

    def capability_summary(self) -> dict[str, object]:
        return self.target.model_dump()

    def prepare_environment(self, plan: ExperimentPlan) -> dict[str, object]:
        return {'target': self.target.name, 'dry_run': plan.dry_run}

    def generate_command(self, plan: ExperimentPlan) -> str:
        return f'execute-plan --plan-id {plan.id} --target {self.target.kind}'

    def submit(self, plan: ExperimentPlan, dry_run: bool = True) -> ExperimentExecution:
        status = ExperimentStatus.SUCCEEDED if dry_run else ExperimentStatus.RUNNING
        completion_log = 'dry-run execution completed' if dry_run else 'execution submitted'
        return ExperimentExecution(
            project_id=plan.project_id,
            plan_id=plan.id,
            target=self.target,
            status=status,
            command=self.generate_command(plan),
            dry_run=dry_run,
            logs=[f'prepared environment for {self.target.name}', completion_log],
        )

    def poll_status(self, execution: ExperimentExecution) -> ExperimentExecution:
        return execution

    def fetch_logs(self, execution: ExperimentExecution) -> list[str]:
        return execution.logs

    def fetch_artifacts(self, execution: ExperimentExecution) -> list[dict[str, object]]:
        execution_dir = self.artifact_root / execution.id
        execution_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = execution_dir / 'summary.json'
        artifact_path.write_text(
            '{"execution_id": "%s", "target": "%s", "status": "%s"}\n'
            % (execution.id, execution.target.name, execution.status),
            encoding='utf-8',
        )
        return [{'kind': 'report', 'path': str(artifact_path)}]

    def cancel(self, execution: ExperimentExecution) -> ExperimentExecution:
        execution.status = ExperimentStatus.CANCELLED
        execution.logs.append('execution cancelled')
        return execution
