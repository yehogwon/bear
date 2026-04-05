from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from bear.domain.enums import PermissionLevel

LLMProviderName = Literal['openai_api', 'openai_oauth', 'claude_api']
CodingAgentProviderName = Literal['codex', 'claude_code', 'opencode']


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
    llm_provider: LLMProviderName = 'openai_api'
    llm_model: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: float = 30.0
    llm_offline_fallback: bool = True
    openai_oauth_auth_file: Path = Field(
        default_factory=lambda: Path('~/.opencode/auth/openai.json').expanduser()
    )
    coding_agent_provider: CodingAgentProviderName = 'codex'
    coding_agent_model: str | None = None
    coding_agent_api_key: str | None = None
    coding_agent_base_url: str | None = None
    coding_agent_timeout_seconds: float = 30.0
    coding_agent_offline_fallback: bool = True

    def resolve_llm_api_key(self) -> str | None:
        if self.llm_api_key is not None:
            return self.llm_api_key
        if self.llm_provider == 'claude_api':
            return os.getenv('ANTHROPIC_API_KEY')
        if self.llm_provider == 'openai_oauth':
            env_token = os.getenv('OPENAI_OAUTH_TOKEN')
            if env_token is not None:
                return env_token
            auth_payload = self._read_auth_payload(self.openai_oauth_auth_file)
            return self._read_first_string(
                auth_payload,
                'access_token',
                'accessToken',
                'api_key',
                'apiKey',
            )
        return os.getenv('OPENAI_API_KEY')

    def resolve_coding_agent_api_key(self) -> str | None:
        if self.coding_agent_api_key is not None:
            return self.coding_agent_api_key
        if self.coding_agent_provider == 'claude_code':
            return os.getenv('ANTHROPIC_API_KEY')
        if self.coding_agent_provider == 'opencode':
            return os.getenv('OPENCODE_API_KEY')
        return os.getenv('OPENAI_API_KEY')

    def _read_auth_payload(self, path: Path) -> dict[str, object]:
        try:
            raw_payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        return raw_payload if isinstance(raw_payload, dict) else {}

    def _read_first_string(self, payload: dict[str, object], *keys: str) -> str | None:
        for key in keys:
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return None
