"""Tests for scripts/convert_to_webp.py."""

import sys
from unittest.mock import patch

from PIL import Image

from convert_to_webp import convert_hero_image, convert_image, parse_args, update_references


class TestParseArgs:
    def test_defaults(self):
        with patch.object(sys, 'argv', ['prog']):
            args = parse_args()
        assert args['dry_run'] is False
        assert args['quality'] == 80
        assert args['max_size'] == 1600
        assert args['thumb_height'] == 400
        assert args['thumbnails'] is True

    def test_dry_run(self):
        with patch.object(sys, 'argv', ['prog', '--dry-run']):
            args = parse_args()
        assert args['dry_run'] is True

    def test_quality(self):
        with patch.object(sys, 'argv', ['prog', '--quality', '90']):
            args = parse_args()
        assert args['quality'] == 90

    def test_max_size(self):
        with patch.object(sys, 'argv', ['prog', '--max-size', '800']):
            args = parse_args()
        assert args['max_size'] == 800

    def test_no_thumbnails(self):
        with patch.object(sys, 'argv', ['prog', '--no-thumbnails']):
            args = parse_args()
        assert args['thumbnails'] is False

    def test_combined_flags(self):
        with patch.object(sys, 'argv', ['prog', '--dry-run', '--quality', '70', '--max-size', '1200']):
            args = parse_args()
        assert args['dry_run'] is True
        assert args['quality'] == 70
        assert args['max_size'] == 1200


class TestConvertImage:
    def test_converts_jpg_to_webp(self, tmp_path):
        gallery_dir = tmp_path / 'gallery'
        gallery_dir.mkdir()
        thumbs_dir = gallery_dir / 'thumbs'
        thumbs_dir.mkdir()

        src = gallery_dir / 'test.jpg'
        img = Image.new('RGB', (200, 100))
        img.save(str(src), 'JPEG')

        args = {'quality': 80, 'max_size': 1600, 'thumbnails': True,
                'thumb_height': 400, 'delete_originals': False}
        result = convert_image(src, gallery_dir, thumbs_dir, args)
        assert result is not None
        webp_path, orig_size, webp_size, thumb_size = result
        assert webp_path.suffix == '.webp'
        assert webp_path.exists()

    def test_resizes_large_image(self, tmp_path):
        gallery_dir = tmp_path / 'gallery'
        gallery_dir.mkdir()

        src = gallery_dir / 'big.jpg'
        img = Image.new('RGB', (3000, 2000))
        img.save(str(src), 'JPEG')

        args = {'quality': 80, 'max_size': 1600, 'thumbnails': False,
                'thumb_height': 400, 'delete_originals': False}
        result = convert_image(src, gallery_dir, None, args)
        assert result is not None

        # Verify the webp was created and is within max size
        webp_path = result[0]
        webp_img = Image.open(webp_path)
        assert max(webp_img.size) <= 1600

    def test_invalid_file(self, tmp_path):
        gallery_dir = tmp_path / 'gallery'
        gallery_dir.mkdir()
        src = gallery_dir / 'bad.jpg'
        src.write_text('not an image')

        args = {'quality': 80, 'max_size': 1600, 'thumbnails': False,
                'thumb_height': 400, 'delete_originals': False}
        result = convert_image(src, gallery_dir, None, args)
        assert result is None


class TestUpdateReferences:
    def test_updates_gallery_yml(self, tmp_path):
        (tmp_path / '_data').mkdir()
        (tmp_path / '_data' / 'gallery.yml').write_text(
            '- image: /assets/img/gallery/photo.jpg\n'
        )

        updated = update_references(tmp_path)
        assert '_data/gallery.yml' in updated
        content = (tmp_path / '_data' / 'gallery.yml').read_text()
        assert '.webp' in content
        assert '.jpg' not in content

    def test_updates_event_files(self, tmp_path):
        (tmp_path / '_events').mkdir()
        (tmp_path / '_events' / 'test.md').write_text(
            '---\nimage: /assets/img/gallery/photo.png\n---\n'
        )

        updated = update_references(tmp_path)
        assert '_events/test.md' in updated

    def test_no_changes_needed(self, tmp_path):
        (tmp_path / '_data').mkdir()
        (tmp_path / '_data' / 'gallery.yml').write_text(
            '- image: /assets/img/gallery/photo.webp\n'
        )
        updated = update_references(tmp_path)
        assert updated == []

    def test_dry_run(self, tmp_path):
        (tmp_path / '_data').mkdir()
        original = '- image: /assets/img/gallery/photo.jpg\n'
        (tmp_path / '_data' / 'gallery.yml').write_text(original)

        updated = update_references(tmp_path, dry_run=True)
        assert len(updated) == 1
        # File should NOT be modified
        assert (tmp_path / '_data' / 'gallery.yml').read_text() == original


class TestConvertHeroImage:
    def test_converts_hero(self, tmp_path):
        img_dir = tmp_path / 'assets' / 'img'
        img_dir.mkdir(parents=True)
        hero = img_dir / 'hero1.jpg'
        img = Image.new('RGB', (200, 100))
        img.save(str(hero), 'JPEG')

        args = {'quality': 80, 'delete_originals': False}
        result = convert_hero_image(tmp_path, args)
        assert result is not None
        assert (img_dir / 'hero1.webp').exists()

    def test_no_hero(self, tmp_path):
        img_dir = tmp_path / 'assets' / 'img'
        img_dir.mkdir(parents=True)
        args = {'quality': 80, 'delete_originals': False}
        result = convert_hero_image(tmp_path, args)
        assert result is None
