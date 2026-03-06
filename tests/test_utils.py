"""Tests for scripts/utils.py."""

import os
from datetime import date

from PIL import Image

from utils import (
    GALLERY_WEB_PREFIX,
    apply_exif_orientation,
    build_event_url,
    ensure_rgb,
    gallery_dated_photos,
    gallery_known_images,
    insert_gallery_dates,
    load_gallery_yaml,
    parse_event_file,
    resize_image,
    slugify,
    update_event_frontmatter,
)

from conftest import write_event_file, write_gallery_yml


# --- slugify ---

class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_underscores(self):
        assert slugify("hello_world") == "hello-world"

    def test_leading_trailing(self):
        assert slugify("  hello world  ") == "hello-world"

    def test_hyphens(self):
        assert slugify("hello---world") == "hello-world"

    def test_empty(self):
        assert slugify("") == ""

    def test_unicode(self):
        assert slugify("café latte") == "café-latte"


# --- load_gallery_yaml ---

class TestLoadGalleryYaml:
    def test_valid_file(self, gallery_yml):
        entries = [{'image': '/assets/img/gallery/a.webp'}]
        write_gallery_yml(gallery_yml, entries)
        result = load_gallery_yaml(str(gallery_yml))
        assert len(result) == 1
        assert result[0]['image'] == '/assets/img/gallery/a.webp'

    def test_missing_file(self, tmp_path):
        result = load_gallery_yaml(str(tmp_path / 'nonexistent.yml'))
        assert result == []

    def test_empty_file(self, gallery_yml):
        gallery_yml.write_text('')
        result = load_gallery_yaml(str(gallery_yml))
        assert result == []


# --- gallery_known_images ---

class TestGalleryKnownImages:
    def test_extracts_images(self):
        entries = [
            {'image': '/a.webp'},
            {'image': '/b.webp'},
            None,
            {'other': 'no image'},
        ]
        result = gallery_known_images(entries)
        assert result == {'/a.webp', '/b.webp'}

    def test_empty(self):
        assert gallery_known_images([]) == set()


# --- gallery_dated_photos ---

class TestGalleryDatedPhotos:
    def test_filters_dated(self):
        entries = [
            {'image': '/a.webp', 'date': date(2024, 6, 15)},
            {'image': '/b.webp'},  # no date
            {'image': '/c.webp', 'date': 'not-a-date'},  # string, not date
            {'image': '/d.webp', 'date': date(2024, 7, 20)},
        ]
        result = gallery_dated_photos(entries)
        assert len(result) == 2
        assert result[0] == ('/a.webp', date(2024, 6, 15))
        assert result[1] == ('/d.webp', date(2024, 7, 20))

    def test_empty(self):
        assert gallery_dated_photos([]) == []


# --- parse_event_file ---

class TestParseEventFile:
    def test_valid_event(self, events_dir):
        path = write_event_file(events_dir, 'test.md', {
            'title': 'Test',
            'date': '2026-06-15',
        })
        result = parse_event_file(path)
        assert result is not None
        meta, fm_raw, rest = result
        assert meta['title'] == 'Test'
        assert 'Event details' in rest

    def test_no_frontmatter(self, events_dir):
        path = os.path.join(str(events_dir), 'bad.md')
        with open(path, 'w') as f:
            f.write("No front matter here.")
        assert parse_event_file(path) is None

    def test_unclosed_frontmatter(self, events_dir):
        path = os.path.join(str(events_dir), 'bad2.md')
        with open(path, 'w') as f:
            f.write("---\ntitle: Test\nNo closing fence")
        assert parse_event_file(path) is None


# --- update_event_frontmatter ---

class TestUpdateEventFrontmatter:
    def test_adds_fields(self, events_dir):
        path = write_event_file(events_dir, 'test.md', {
            'title': 'Test',
            'date': '2026-06-15',
        })
        result = parse_event_file(path)
        meta, fm_raw, rest = result

        update_event_frontmatter(path, fm_raw, rest, {
            'emailed': '2026-03-06',
            'posted_x': 'https://x.com/123',
        })

        result2 = parse_event_file(path)
        meta2, _, _ = result2
        assert meta2['emailed'] == '2026-03-06'
        assert meta2['posted_x'] == 'https://x.com/123'
        assert meta2['title'] == 'Test'


# --- build_event_url ---

class TestBuildEventUrl:
    def test_basic(self):
        url = build_event_url('2026-03-15-my-event.md', 'https://example.com')
        assert url == 'https://example.com/events/2026/03/my-event/'

    def test_multi_word_slug(self):
        url = build_event_url('2026-01-01-new-years-ride.md', 'https://spp.com')
        assert url == 'https://spp.com/events/2026/01/new-years-ride/'


# --- insert_gallery_dates ---

class TestInsertGalleryDates:
    def test_inserts_dates(self, gallery_yml):
        content = (
            "- image: /assets/img/gallery/a.webp\n"
            "- image: /assets/img/gallery/b.webp\n"
        )
        gallery_yml.write_text(content)

        pairs = [
            ({'image': '/assets/img/gallery/a.webp'}, date(2024, 6, 15)),
        ]
        insert_gallery_dates(str(gallery_yml), pairs)

        result = gallery_yml.read_text()
        assert '  date: 2024-06-15' in result
        # b.webp should not have a date added
        lines = result.strip().split('\n')
        b_idx = next(i for i, line in enumerate(lines) if 'b.webp' in line)
        # Next line after b.webp should not be a date line
        if b_idx + 1 < len(lines):
            assert 'date:' not in lines[b_idx + 1]


# --- apply_exif_orientation ---

class TestApplyExifOrientation:
    def test_no_exif(self):
        img = Image.new('RGB', (100, 50))
        result = apply_exif_orientation(img)
        assert result.size == (100, 50)

    def test_returns_image(self):
        img = Image.new('RGB', (100, 50))
        result = apply_exif_orientation(img)
        assert isinstance(result, Image.Image)


# --- resize_image ---

class TestResizeImage:
    def test_landscape_too_large(self):
        img = Image.new('RGB', (2000, 1000))
        result = resize_image(img, 1600)
        assert result.size[0] == 1600
        assert result.size[1] == 800

    def test_portrait_too_large(self):
        img = Image.new('RGB', (1000, 2000))
        result = resize_image(img, 1600)
        assert result.size[0] == 800
        assert result.size[1] == 1600

    def test_already_small(self):
        img = Image.new('RGB', (800, 600))
        result = resize_image(img, 1600)
        assert result.size == (800, 600)

    def test_exact_size(self):
        img = Image.new('RGB', (1600, 1600))
        result = resize_image(img, 1600)
        assert result.size == (1600, 1600)


# --- ensure_rgb ---

class TestEnsureRgb:
    def test_rgba_to_rgb(self):
        img = Image.new('RGBA', (10, 10))
        result = ensure_rgb(img)
        assert result.mode == 'RGB'

    def test_rgb_passthrough(self):
        img = Image.new('RGB', (10, 10))
        result = ensure_rgb(img)
        assert result.mode == 'RGB'

    def test_palette_to_rgb(self):
        img = Image.new('P', (10, 10))
        result = ensure_rgb(img)
        assert result.mode == 'RGB'

    def test_la_to_rgb(self):
        img = Image.new('LA', (10, 10))
        result = ensure_rgb(img)
        assert result.mode == 'RGB'


# --- GALLERY_WEB_PREFIX ---

def test_gallery_web_prefix():
    assert GALLERY_WEB_PREFIX == "/assets/img/gallery/"
