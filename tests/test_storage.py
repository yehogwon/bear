from pathlib import Path

from bear.storage.markdown import MarkdownRepository


def test_markdown_repository_round_trip(tmp_path: Path) -> None:
    repository = MarkdownRepository(tmp_path / 'state')
    payload = {
        'id': 'proj_123',
        'name': 'Project A',
        'tags': ['demo'],
        'metadata': {'priority': 'high'},
    }

    repository.save('projects', payload['id'], payload)

    assert repository.get('projects', payload['id']) == payload
    saved_file = tmp_path / 'state' / 'projects' / 'proj_123.md'
    assert saved_file.exists()
    assert saved_file.read_text(encoding='utf-8').startswith('# Project A\n\n```json\n')


def test_markdown_repository_returns_none_for_missing_record(tmp_path: Path) -> None:
    repository = MarkdownRepository(tmp_path / 'state')

    assert repository.get('projects', 'missing') is None


def test_markdown_repository_lists_empty_namespace(tmp_path: Path) -> None:
    repository = MarkdownRepository(tmp_path / 'state')

    assert repository.list('projects') == []


def test_markdown_repository_lists_records_in_sorted_order(tmp_path: Path) -> None:
    repository = MarkdownRepository(tmp_path / 'state')
    repository.save('projects', 'proj_b', {'id': 'proj_b', 'name': 'Project B'})
    repository.save('projects', 'proj_a', {'id': 'proj_a', 'name': 'Project A'})

    records = repository.list('projects')

    assert [record['id'] for record in records] == ['proj_a', 'proj_b']
