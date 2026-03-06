"""Shared fixtures for tests."""

import os

import pytest
import yaml


@pytest.fixture
def repo_root(tmp_path):
    """Create a minimal repo structure in tmp_path."""
    (tmp_path / '_data').mkdir()
    (tmp_path / '_events').mkdir()
    (tmp_path / 'assets' / 'img' / 'gallery').mkdir(parents=True)
    return tmp_path


@pytest.fixture
def gallery_yml(repo_root):
    """Path to a gallery.yml in the temp repo."""
    return repo_root / '_data' / 'gallery.yml'


@pytest.fixture
def events_dir(repo_root):
    """Path to _events/ in the temp repo."""
    return repo_root / '_events'


@pytest.fixture
def sample_gallery_entries():
    """Sample gallery entries for testing."""
    return [
        {'image': '/assets/img/gallery/photo1.webp', 'date': '2024-06-15'},
        {'image': '/assets/img/gallery/photo2.webp'},
        {'image': '/assets/img/gallery/photo3.webp', 'date': '2024-07-20'},
    ]


def write_gallery_yml(path, entries):
    """Helper to write gallery entries to a YAML file."""
    with open(path, 'w') as f:
        yaml.dump(entries, f, default_flow_style=False)


def write_event_file(events_dir, filename, meta, body="Event details here."):
    """Helper to write an event markdown file."""
    filepath = os.path.join(str(events_dir), filename)
    fm_lines = []
    for key, value in meta.items():
        if isinstance(value, str) and ' ' in value:
            fm_lines.append(f'{key}: "{value}"')
        else:
            fm_lines.append(f'{key}: {value}')
    content = '---\n' + '\n'.join(fm_lines) + '\n---\n' + body + '\n'
    with open(filepath, 'w') as f:
        f.write(content)
    return filepath
