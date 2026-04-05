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


def _offline_patch_plan(provider_name: str, objective: str) -> str:
    focus = _compact_text(objective, limit=180)
    emphasis_by_provider = {
        'codex': 'Favor the smallest reversible diff and add tests before broadening scope.',
        'claude_code': 'Call out notable risks, shared-file hotspots, and verification evidence.',
        'opencode': (
            'Keep the plan compatible with OpenAI-style local endpoints and simple prompts.'
        ),
    }
    emphasis = emphasis_by_provider.get(
        provider_name,
        'Keep the change narrow and verifiable.',
    )
    steps = [
        f'Clarify the success condition for: {focus}',
        'Inspect the narrowest runtime, config, and provider wiring surfaces that can satisfy it.',
        'Implement the smallest provider-aware change that activates the chosen backend.',
        'Add or update tests that prove selection, request shaping, and output consumption.',
        'Run lint and targeted verification before expanding scope.',
    ]
    numbered_steps = '\n'.join(f'{index}. {step}' for index, step in enumerate(steps, start=1))
    return f'{provider_name} offline patch plan:\n{numbered_steps}\nNote: {emphasis}'


@dataclass(slots=True)
class _BaseCodingAgentBackend:
    provider_name: str
    model: str
    api_key: str | None
    base_url: str | None
    timeout_seconds: float = 30.0
    offline_fallback: bool = True
    transport: JsonTransport = field(default=json_post, repr=False)

    def create_patch_plan(self, objective: str) -> str:
        normalized_objective = ' '.join(objective.split())
        if not normalized_objective:
            raise ValueError('Objective must not be empty.')
        if self._can_call_remote():
            try:
                return self._generate_remote(normalized_objective)
            except RuntimeError:
                if not self.offline_fallback:
                    raise
        elif not self.offline_fallback:
            raise RuntimeError(
                f'{self.provider_name} is not configured for remote calls and '
                'offline fallback is disabled.'
            )
        return _offline_patch_plan(self.provider_name, normalized_objective)

    def _can_call_remote(self) -> bool:
        return self.api_key is not None and self.base_url is not None

    def _generate_remote(self, _objective: str) -> str:
        raise NotImplementedError


class CodexBackend(_BaseCodingAgentBackend):
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
            provider_name='codex',
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )

    def _generate_remote(self, objective: str) -> str:
        payload = {
            'model': self.model,
            'instructions': (
                'You are a coding agent. Produce a concise, test-first patch plan in plain text '
                'with files to inspect, edits to make, and verification to run.'
            ),
            'input': objective,
        }
        response = self.transport(
            join_url(self.base_url or '', 'responses'),
            {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            payload,
            self.timeout_seconds,
        )
        return extract_openai_output_text(response)


class ClaudeCodeBackend(_BaseCodingAgentBackend):
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
            provider_name='claude_code',
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )

    def _generate_remote(self, objective: str) -> str:
        payload = {
            'model': self.model,
            'max_tokens': 900,
            'messages': [
                {
                    'role': 'user',
                    'content': (
                        'Create a concise, test-first patch plan with files to inspect, '
                        'edits to make, '
                        f'risks, and verification steps. Objective: {objective}'
                    ),
                }
            ],
        }
        response = self.transport(
            join_url(self.base_url or '', 'v1/messages'),
            {
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01',
                'x-api-key': self.api_key or '',
            },
            payload,
            self.timeout_seconds,
        )
        return extract_anthropic_output_text(response)


class OpenCodeBackend(_BaseCodingAgentBackend):
    def __init__(
        self,
        *,
        model: str = 'gpt-4.1',
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
        offline_fallback: bool = True,
        transport: JsonTransport = json_post,
    ) -> None:
        super().__init__(
            provider_name='opencode',
            model=model,
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            offline_fallback=offline_fallback,
            transport=transport,
        )

    def _can_call_remote(self) -> bool:
        return self.base_url is not None

    def _generate_remote(self, objective: str) -> str:
        headers = {'Content-Type': 'application/json'}
        if self.api_key is not None:
            headers['Authorization'] = f'Bearer {self.api_key}'
        payload = {
            'model': self.model,
            'instructions': (
                'You are an OpenAI-compatible coding planner. '
                'Return a concise plain-text patch plan '
                'with the minimal edits and verification steps.'
            ),
            'input': objective,
        }
        response = self.transport(
            join_url(self.base_url or '', 'responses'),
            headers,
            payload,
            self.timeout_seconds,
        )
        return extract_openai_output_text(response)
