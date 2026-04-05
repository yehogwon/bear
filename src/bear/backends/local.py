from bear.backends.base import BaseExecutionBackend
from bear.domain.enums import ExecutionBackendKind
from bear.domain.models import BackendTarget


class LocalExecutionBackend(BaseExecutionBackend):
    def __init__(self) -> None:
        super().__init__(
            BackendTarget(name='local-process', kind=ExecutionBackendKind.LOCAL, supports_gpu=False)
        )


class LocalCUDAExecutionBackend(BaseExecutionBackend):
    def __init__(self) -> None:
        super().__init__(
            BackendTarget(
                name='local-cuda', kind=ExecutionBackendKind.LOCAL_CUDA, supports_gpu=True
            )
        )
