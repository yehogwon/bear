from pathlib import Path

from bear.backends.base import BaseExecutionBackend
from bear.domain.enums import ExecutionBackendKind
from bear.domain.models import BackendTarget


class SlurmExecutionBackend(BaseExecutionBackend):
    def __init__(self, artifact_root: str | Path = '.bear/artifacts') -> None:
        super().__init__(
            BackendTarget(name='slurm', kind=ExecutionBackendKind.SLURM, supports_gpu=True),
            artifact_root=artifact_root,
        )


class KubeflowExecutionBackend(BaseExecutionBackend):
    def __init__(self, artifact_root: str | Path = '.bear/artifacts') -> None:
        super().__init__(
            BackendTarget(name='kubeflow', kind=ExecutionBackendKind.KUBEFLOW, supports_gpu=True),
            artifact_root=artifact_root,
        )
