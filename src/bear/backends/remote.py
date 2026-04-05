from bear.backends.base import BaseExecutionBackend
from bear.domain.enums import ExecutionBackendKind
from bear.domain.models import BackendTarget


class SlurmExecutionBackend(BaseExecutionBackend):
    def __init__(self) -> None:
        super().__init__(
            BackendTarget(name='slurm', kind=ExecutionBackendKind.SLURM, supports_gpu=True)
        )


class KubeflowExecutionBackend(BaseExecutionBackend):
    def __init__(self) -> None:
        super().__init__(
            BackendTarget(name='kubeflow', kind=ExecutionBackendKind.KUBEFLOW, supports_gpu=True)
        )
