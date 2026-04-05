from enum import StrEnum


class PermissionLevel(StrEnum):
    ALLOW = 'allow'
    REQUEST = 'request'
    DISALLOW = 'disallow'


class RiskLevel(StrEnum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'


class ExperimentStatus(StrEnum):
    PLANNED = 'planned'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ApprovalStatus(StrEnum):
    PENDING = 'pending'
    APPROVED = 'approved'
    REJECTED = 'rejected'


class ExecutionBackendKind(StrEnum):
    LOCAL = 'local'
    LOCAL_CUDA = 'local_cuda'
    SLURM = 'slurm'
    KUBEFLOW = 'kubeflow'
