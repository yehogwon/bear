import json
from collections.abc import Mapping
from pathlib import Path

from bear.config.settings import Settings
from bear.providers.coding_agents.base import ClaudeCodeBackend, CodexBackend, OpenCodeBackend
from bear.providers.llm.base import ClaudeAPIBackend, OpenAIAPIBackend


def test_openai_oauth_reads_token_from_opencode_auth_file(tmp_path: Path) -> None:
    auth_file = tmp_path / 'openai.json'
    _ = auth_file.write_text(json.dumps({'access_token': 'oauth-token'}))

    settings = Settings(
        llm_provider='openai_oauth',
        openai_oauth_auth_file=auth_file,
    )

    assert settings.resolve_llm_api_key() == 'oauth-token'


def test_openai_api_backend_calls_responses_api() -> None:
    captured: dict[str, object] = {}

    def transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        captured['url'] = url
        captured['headers'] = headers
        captured['payload'] = payload
        captured['timeout_seconds'] = timeout_seconds
        return {
            'output': [
                {
                    'content': [
                        {
                            'type': 'output_text',
                            'text': 'openai planning summary',
                        }
                    ]
                }
            ]
        }

    backend = OpenAIAPIBackend(
        api_key='test-key',
        model='gpt-test',
        offline_fallback=False,
        transport=transport,
    )

    response = backend.generate_text('Plan a provider-aware dry run.')

    assert response == 'openai planning summary'
    assert captured['url'] == 'https://api.openai.com/v1/responses'
    assert captured['timeout_seconds'] == 30.0
    assert captured['headers'] == {
        'Authorization': 'Bearer test-key',
        'Content-Type': 'application/json',
    }
    assert captured['payload'] == {
        'model': 'gpt-test',
        'instructions': 'You are a concise research planning assistant. Return plain text only.',
        'input': 'Plan a provider-aware dry run.',
    }


def test_claude_api_backend_calls_messages_api() -> None:
    captured: dict[str, object] = {}

    def transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        captured['url'] = url
        captured['headers'] = headers
        captured['payload'] = payload
        captured['timeout_seconds'] = timeout_seconds
        return {'content': [{'type': 'text', 'text': 'claude analysis'}]}

    backend = ClaudeAPIBackend(
        api_key='anthropic-test-key',
        model='claude-test',
        offline_fallback=False,
        transport=transport,
    )

    response = backend.generate_text('Summarize the latest execution evidence.')

    assert response == 'claude analysis'
    assert captured['url'] == 'https://api.anthropic.com/v1/messages'
    assert captured['timeout_seconds'] == 30.0
    assert captured['headers'] == {
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01',
        'x-api-key': 'anthropic-test-key',
    }
    assert captured['payload'] == {
        'model': 'claude-test',
        'max_tokens': 700,
        'messages': [{'role': 'user', 'content': 'Summarize the latest execution evidence.'}],
    }


def test_codex_backend_calls_responses_api_for_patch_plan() -> None:
    captured: dict[str, object] = {}

    def transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        captured['url'] = url
        captured['headers'] = headers
        captured['payload'] = payload
        captured['timeout_seconds'] = timeout_seconds
        return {
            'output': [
                {
                    'content': [
                        {
                            'type': 'output_text',
                            'text': '1. Inspect service.py\n2. Wire settings\n3. Add tests',
                        }
                    ]
                }
            ]
        }

    backend = CodexBackend(
        api_key='test-key',
        model='gpt-codex-test',
        offline_fallback=False,
        transport=transport,
    )

    response = backend.create_patch_plan('Wire provider selection into the runtime service.')

    assert response == '1. Inspect service.py\n2. Wire settings\n3. Add tests'
    assert captured['url'] == 'https://api.openai.com/v1/responses'
    assert captured['timeout_seconds'] == 30.0
    assert captured['headers'] == {
        'Authorization': 'Bearer test-key',
        'Content-Type': 'application/json',
    }
    assert captured['payload'] == {
        'model': 'gpt-codex-test',
        'instructions': (
            'You are a coding agent. Produce a concise, test-first patch plan in plain text '
            'with files to inspect, edits to make, and verification to run.'
        ),
        'input': 'Wire provider selection into the runtime service.',
    }


def test_claude_code_backend_calls_messages_api_for_patch_plan() -> None:
    captured: dict[str, object] = {}

    def transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        captured['url'] = url
        captured['headers'] = headers
        captured['payload'] = payload
        captured['timeout_seconds'] = timeout_seconds
        return {'content': [{'type': 'text', 'text': '1. Review service.py\n2. Add risks'}]}

    backend = ClaudeCodeBackend(
        api_key='anthropic-test-key',
        model='claude-code-test',
        offline_fallback=False,
        transport=transport,
    )

    response = backend.create_patch_plan('Add provider wiring risks to the patch plan.')

    assert response == '1. Review service.py\n2. Add risks'
    assert captured['url'] == 'https://api.anthropic.com/v1/messages'
    assert captured['timeout_seconds'] == 30.0
    assert captured['headers'] == {
        'content-type': 'application/json',
        'anthropic-version': '2023-06-01',
        'x-api-key': 'anthropic-test-key',
    }
    assert captured['payload'] == {
        'model': 'claude-code-test',
        'max_tokens': 900,
        'messages': [
            {
                'role': 'user',
                'content': (
                    'Create a concise, test-first patch plan with files to inspect, edits to make, '
                    'risks, and verification steps. Objective: Add provider wiring risks to the '
                    'patch plan.'
                ),
            }
        ],
    }


def test_opencode_backend_uses_custom_openai_compatible_base_url() -> None:
    captured: dict[str, object] = {}

    def transport(
        url: str,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        captured['url'] = url
        captured['headers'] = headers
        captured['payload'] = payload
        captured['timeout_seconds'] = timeout_seconds
        return {'output': [{'content': [{'type': 'output_text', 'text': 'local patch plan'}]}]}

    backend = OpenCodeBackend(
        base_url='http://127.0.0.1:11434/v1',
        model='local-coder',
        offline_fallback=False,
        transport=transport,
    )

    response = backend.create_patch_plan('Use a local OpenAI-compatible planner.')

    assert response == 'local patch plan'
    assert captured['url'] == 'http://127.0.0.1:11434/v1/responses'
    assert captured['timeout_seconds'] == 30.0
    assert captured['headers'] == {'Content-Type': 'application/json'}
    assert captured['payload'] == {
        'model': 'local-coder',
        'instructions': (
            'You are an OpenAI-compatible coding planner. Return a concise plain-text patch plan '
            'with the minimal edits and verification steps.'
        ),
        'input': 'Use a local OpenAI-compatible planner.',
    }
