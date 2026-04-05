from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class _BaseCodingAgentBackend:
    provider_name: str

    def create_patch_plan(self, objective: str) -> str:
        return f'[{self.provider_name}] proposed patch plan for: {objective}'


class CodexBackend(_BaseCodingAgentBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='codex')


class ClaudeCodeBackend(_BaseCodingAgentBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='claude_code')


class OpenCodeBackend(_BaseCodingAgentBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='opencode')
