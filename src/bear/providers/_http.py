from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from urllib import error, request

JsonDict = dict[str, object]
JsonTransport = Callable[[str, Mapping[str, str], Mapping[str, object], float], JsonDict]


def json_post(
    url: str,
    headers: Mapping[str, str],
    payload: Mapping[str, object],
    timeout_seconds: float,
) -> JsonDict:
    body = json.dumps(payload).encode('utf-8')
    http_request = request.Request(url, data=body, headers=dict(headers), method='POST')
    try:
        with request.urlopen(http_request, timeout=timeout_seconds) as response:
            raw_body = response.read().decode('utf-8')
    except error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')
        raise RuntimeError(
            f'Provider request to {url} failed with HTTP {exc.code}: {error_body}'
        ) from exc
    except error.URLError as exc:
        raise RuntimeError(f'Provider request to {url} failed: {exc.reason}') from exc

    try:
        decoded = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f'Provider request to {url} returned invalid JSON.') from exc
    if not isinstance(decoded, dict):
        raise RuntimeError(f'Provider request to {url} returned a non-object response.')
    return decoded


def join_url(base_url: str, path: str) -> str:
    return f'{base_url.rstrip("/")}/{path.lstrip("/")}'


def extract_openai_output_text(payload: JsonDict) -> str:
    output_text = payload.get('output_text')
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    output = payload.get('output')
    if not isinstance(output, list):
        raise RuntimeError('OpenAI response did not include an output list.')

    text_parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get('content')
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get('type') != 'output_text':
                continue
            text = part.get('text')
            if isinstance(text, str) and text.strip():
                text_parts.append(text.strip())

    if not text_parts:
        raise RuntimeError('OpenAI response did not include output text.')
    return '\n'.join(text_parts)


def extract_anthropic_output_text(payload: JsonDict) -> str:
    content = payload.get('content')
    if not isinstance(content, list):
        raise RuntimeError('Anthropic response did not include a content list.')

    text_parts: list[str] = []
    for part in content:
        if not isinstance(part, dict) or part.get('type') != 'text':
            continue
        text = part.get('text')
        if isinstance(text, str) and text.strip():
            text_parts.append(text.strip())

    if not text_parts:
        raise RuntimeError('Anthropic response did not include text content.')
    return '\n'.join(text_parts)
