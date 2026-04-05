from __future__ import annotations

import json
from pathlib import Path

JsonDict = dict[str, object]


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


class MarkdownRepository:
    def __init__(self, state_root: str | Path) -> None:
        self.state_root = Path(state_root)
        ensure_directory(self.state_root)

    def save(self, namespace: str, model_id: str, payload: JsonDict) -> None:
        namespace_dir = self.state_root / namespace
        ensure_directory(namespace_dir)
        file_path = namespace_dir / f'{model_id}.md'
        file_path.write_text(self._render_markdown(payload), encoding='utf-8')

    def get(self, namespace: str, model_id: str) -> JsonDict | None:
        file_path = self.state_root / namespace / f'{model_id}.md'
        if not file_path.exists():
            return None
        return self._parse_markdown(file_path.read_text(encoding='utf-8'))

    def list(self, namespace: str) -> list[JsonDict]:
        namespace_dir = self.state_root / namespace
        if not namespace_dir.exists():
            return []
        return [
            self._parse_markdown(file_path.read_text(encoding='utf-8'))
            for file_path in sorted(namespace_dir.glob('*.md'))
        ]

    def _render_markdown(self, payload: JsonDict) -> str:
        title = payload.get('title') or payload.get('name') or payload.get('id') or 'record'
        body = json.dumps(payload, indent=2, sort_keys=True, default=str)
        return f'# {title}\n\n```json\n{body}\n```\n'

    def _parse_markdown(self, content: str) -> JsonDict:
        marker = '```json\n'
        start = content.index(marker) + len(marker)
        end = content.index('\n```', start)
        return dict(json.loads(content[start:end]))
