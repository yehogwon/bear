from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class _BaseLLMBackend:
    provider_name: str

    def generate_text(self, prompt: str) -> str:
        return f'[{self.provider_name}] stub response for: {prompt[:60]}'


class OpenAIAPIBackend(_BaseLLMBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='openai_api')


class OpenAIOAuthBackend(_BaseLLMBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='openai_oauth')


class ClaudeAPIBackend(_BaseLLMBackend):
    def __init__(self) -> None:
        super().__init__(provider_name='claude_api')
