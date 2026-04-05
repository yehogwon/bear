from __future__ import annotations

from bear.config.settings import Settings
from bear.core.interfaces import CodingAgentBackend, LLMBackend
from bear.providers.coding_agents import ClaudeCodeBackend, CodexBackend, OpenCodeBackend
from bear.providers.llm import ClaudeAPIBackend, OpenAIAPIBackend, OpenAIOAuthBackend


def build_llm_backend(settings: Settings) -> LLMBackend:
    if settings.llm_provider == 'openai_api':
        return OpenAIAPIBackend(
            model=settings.llm_model or 'gpt-4.1',
            api_key=settings.resolve_llm_api_key(),
            base_url=settings.llm_base_url or 'https://api.openai.com/v1',
            timeout_seconds=settings.llm_timeout_seconds,
            offline_fallback=settings.llm_offline_fallback,
        )
    if settings.llm_provider == 'openai_oauth':
        return OpenAIOAuthBackend(
            model=settings.llm_model or 'gpt-4.1',
            api_key=settings.resolve_llm_api_key(),
            base_url=settings.llm_base_url or 'https://api.openai.com/v1',
            timeout_seconds=settings.llm_timeout_seconds,
            offline_fallback=settings.llm_offline_fallback,
        )
    if settings.llm_provider == 'claude_api':
        return ClaudeAPIBackend(
            model=settings.llm_model or 'claude-sonnet-4-20250514',
            api_key=settings.resolve_llm_api_key(),
            base_url=settings.llm_base_url or 'https://api.anthropic.com',
            timeout_seconds=settings.llm_timeout_seconds,
            offline_fallback=settings.llm_offline_fallback,
        )
    raise ValueError(f'Unsupported LLM provider: {settings.llm_provider}')


def build_coding_agent_backend(settings: Settings) -> CodingAgentBackend:
    if settings.coding_agent_provider == 'codex':
        return CodexBackend(
            model=settings.coding_agent_model or 'gpt-4.1',
            api_key=settings.resolve_coding_agent_api_key(),
            base_url=settings.coding_agent_base_url or 'https://api.openai.com/v1',
            timeout_seconds=settings.coding_agent_timeout_seconds,
            offline_fallback=settings.coding_agent_offline_fallback,
        )
    if settings.coding_agent_provider == 'claude_code':
        return ClaudeCodeBackend(
            model=settings.coding_agent_model or 'claude-sonnet-4-20250514',
            api_key=settings.resolve_coding_agent_api_key(),
            base_url=settings.coding_agent_base_url or 'https://api.anthropic.com',
            timeout_seconds=settings.coding_agent_timeout_seconds,
            offline_fallback=settings.coding_agent_offline_fallback,
        )
    if settings.coding_agent_provider == 'opencode':
        return OpenCodeBackend(
            model=settings.coding_agent_model or 'gpt-4.1',
            api_key=settings.resolve_coding_agent_api_key(),
            base_url=settings.coding_agent_base_url,
            timeout_seconds=settings.coding_agent_timeout_seconds,
            offline_fallback=settings.coding_agent_offline_fallback,
        )
    raise ValueError(f'Unsupported coding-agent provider: {settings.coding_agent_provider}')
