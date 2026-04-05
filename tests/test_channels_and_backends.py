from bear.backends.local import LocalCUDAExecutionBackend
from bear.backends.remote import KubeflowExecutionBackend, SlurmExecutionBackend
from bear.channels.base import DiscordChannel, LocalWebChannel
from bear.domain.enums import ExecutionBackendKind
from bear.domain.models import BackendTarget, ExperimentPlan


def test_channels_return_outbound_messages() -> None:
    local_message = LocalWebChannel().send_message('hello web')
    discord_message = DiscordChannel().send_message('hello discord')

    assert local_message.channel == 'local_web'
    assert local_message.direction == 'outbound'
    assert local_message.body == 'hello web'
    assert discord_message.channel == 'discord'
    assert discord_message.direction == 'outbound'
    assert discord_message.body == 'hello discord'


def test_local_cuda_backend_reports_gpu_capabilities() -> None:
    backend = LocalCUDAExecutionBackend()

    assert backend.target.kind == ExecutionBackendKind.LOCAL_CUDA
    assert backend.target.supports_gpu is True
    assert backend.capability_summary()['name'] == 'local-cuda'


def test_remote_backends_expose_expected_targets() -> None:
    slurm = SlurmExecutionBackend()
    kubeflow = KubeflowExecutionBackend()

    assert slurm.target.kind == ExecutionBackendKind.SLURM
    assert slurm.target.supports_gpu is True
    assert kubeflow.target.kind == ExecutionBackendKind.KUBEFLOW
    assert kubeflow.target.supports_gpu is True


def test_backend_fetch_artifacts_uses_execution_id_path() -> None:
    backend = SlurmExecutionBackend()
    plan = ExperimentPlan(
        project_id='proj_123',
        hypothesis_id='hyp_123',
        title='Plan',
        objective='Run',
        target=BackendTarget(name='slurm', kind=ExecutionBackendKind.SLURM, supports_gpu=True),
    )
    execution = backend.submit(plan, dry_run=False)

    artifacts = backend.fetch_artifacts(execution)

    assert artifacts == [{'kind': 'report', 'path': f'artifacts/{execution.id}/summary.json'}]
