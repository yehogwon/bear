from __future__ import annotations

from dataclasses import dataclass, field

from bear.providers._http import (
    JsonTransport,
    extract_anthropic_output_text,
    extract_openai_output_text,
    join_url,
    json_post,
)


def _compact_text(text: str, *, limit: int) -> str:
    compact = ' '.join(text.split())
    if len(compact) <= limit:
        return compact
    return f'{compact[: limit - 1].rstrip()}…'


@dataclass(slots=True)
class _BaseLLMBackend:
    provider_name: str
    model: str
    api_key: str | None
    base_url: str
    timeout_seconds: float = 30.0
    offline_fallback: bool = True
    transport: JsonTransport = field(default=json_post, repr=False)

    def generate_text(self, prompt: str) -> str:
        normalized_prompt = ' '.join(prompt.split())
        if not normalized_prompt:
            raise ValueError('Prompt must not be empty.')
        if self._can_call_remote():
            try:
                return self._generate_remote(normalized_prompt)
            except RuntimeError:
                if not self.offline_fallback:
                    raise
        elif not self.offline_fallback:
            raise RuntimeError(
                f'{self.provider_name} is not configured for remote calls and '
                'offline fallback is disabled.'
            )
        return self._generate_offline(normalized_prompt)

    def _can_call_remote(self) -> bool:
        return self.api_key is not None

    def _generate_remote(self, _prompt: str) -> str:
        raise NotImplementedError

    def _generate_offline(self, prompt: str) -> str:
        focus = _compact_text(prompt, limit=200)
        return (
            f'{self.provider_name} offline synthesis: {focus}. '
            'Recommended framing: define the measurable outcome, keep the scope narrow, '
            'and record the next verification step.'
        )


class OpenAIAPIBackend(_BaseLLMBackend):
    def __init__(
        self,
        *,
        model: str = 'gpt-4.1',
        api_key: str | None = None,
        base_url: str = 'https://api.openai.com/v1',
        timeout_seconds: float = 30.0,
        offline_fallback: bool = True,
        transport: JsonTransport = json_post,
    ) -> None:
        super().__init__(
            provider_name='openai_api',
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )

    def _generate_remote(self, prompt: str) -> str:
        payload = {
            'model': self.model,
            'instructions': (
                'You are a concise research planning assistant. Return plain text only.'
            ),
            'input': prompt,
        }
        response = self.transport(
            join_url(self.base_url, 'responses'),
            {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            payload,
            self.timeout_seconds,
        )
        return extract_openai_output_text(response)


class OpenAIOAuthBackend(OpenAIAPIBackend):
    def __init__(
        self,
        *,
        model: str = 'gpt-4.1',
        api_key: str | None = None,
        base_url: str = 'https://api.openai.com/v1',
        timeout_seconds: float = 30.0,
        offline_fallback: bool = True,
        transport: JsonTransport = json_post,
    ) -> None:
        super().__init__(
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )
        self.provider_name = 'openai_oauth'


class ClaudeAPIBackend(_BaseLLMBackend):
    def __init__(
        self,
        *,
        model: str = 'claude-sonnet-4-20250514',
        api_key: str | None = None,
        base_url: str = 'https://api.anthropic.com',
        timeout_seconds: float = 30.0,
        offline_fallback: bool = True,
        transport: JsonTransport = json_post,
    ) -> None:
        super().__init__(
            provider_name='claude_api',
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )

    def _generate_remote(self, prompt: str) -> str:
        payload = {
            'model': self.model,
            'max_tokens': 700,
            'messages': [{'role': 'user', 'content': prompt}],
        }
        response = self.transport(
            join_url(self.base_url, 'v1/messages'),
            {
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01',
                'x-api-key': self.api_key or '',
            },
            payload,
            self.timeout_seconds,
        )
        return extract_anthropic_output_text(response)
