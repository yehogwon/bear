from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from bear.domain.enums import PermissionLevel


class Settings(BaseModel):
    state_root: Path = Path('.bear/state')
    artifact_root: Path = Path('.bear/artifacts')
    host: str = '127.0.0.1'
    port: int = 8000
    default_permissions: dict[str, PermissionLevel] = Field(
        default_factory=lambda: {
            'read': PermissionLevel.ALLOW,
            'edit': PermissionLevel.REQUEST,
            'run_experiment': PermissionLevel.REQUEST,
            'submit_slurm_job': PermissionLevel.REQUEST,
            'notify_human': PermissionLevel.ALLOW,
        }
    )
    context_permissions: dict[str, dict[str, PermissionLevel]] = Field(
        default_factory=lambda: {
            'dry_run': {
                'run_experiment': PermissionLevel.ALLOW,
            }
        }
    )
