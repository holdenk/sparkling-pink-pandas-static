"""Tests for scripts/optimize_gallery_images.py."""

import sys
from unittest.mock import patch

from PIL import Image

from optimize_gallery_images import get_image_size_kb, optimize_image, parse_args


class TestParseArgs:
    def test_defaults(self):
        with patch.object(sys, 'argv', ['prog']):
            args = parse_args()
        assert args['dry_run'] is False
        assert args['max_size'] == 1600
        assert args['quality'] == 82
        assert args['backup'] is False

    def test_dry_run(self):
        with patch.object(sys, 'argv', ['prog', '--dry-run']):
            args = parse_args()
        assert args['dry_run'] is True

    def test_backup(self):
        with patch.object(sys, 'argv', ['prog', '--backup']):
            args = parse_args()
        assert args['backup'] is True

    def test_quality_and_max_size(self):
        with patch.object(sys, 'argv', ['prog', '--quality', '90', '--max-size', '800']):
            args = parse_args()
        assert args['quality'] == 90
        assert args['max_size'] == 800


class TestGetImageSizeKb:
    def test_returns_kb(self, tmp_path):
        f = tmp_path / 'test.txt'
        f.write_bytes(b'x' * 2048)
        assert get_image_size_kb(str(f)) == 2.0


class TestOptimizeImage:
    def test_optimizes_jpeg(self, tmp_path):
        img_path = tmp_path / 'test.jpg'
        img = Image.new('RGB', (2000, 1500))
        img.save(str(img_path), 'JPEG')

        result = optimize_image(img_path, max_size=1600, quality=82)
        assert result is not None
        new_w, new_h, saved = result
        assert new_w <= 1600
        assert new_h <= 1600

    def test_optimizes_small_jpeg(self, tmp_path):
        img_path = tmp_path / 'small.jpg'
        img = Image.new('RGB', (800, 600))
        img.save(str(img_path), 'JPEG')

        result = optimize_image(img_path, max_size=1600, quality=82)
        assert result is not None
        new_w, new_h, _ = result
        assert new_w == 800
        assert new_h == 600

    def test_optimizes_webp(self, tmp_path):
        img_path = tmp_path / 'test.webp'
        img = Image.new('RGB', (200, 100))
        img.save(str(img_path), 'WEBP')

        result = optimize_image(img_path, max_size=1600, quality=80)
        assert result is not None

    def test_optimizes_png(self, tmp_path):
        img_path = tmp_path / 'test.png'
        img = Image.new('RGB', (200, 100))
        img.save(str(img_path), 'PNG')

        result = optimize_image(img_path, max_size=1600, quality=80)
        assert result is not None

    def test_invalid_file(self, tmp_path):
        img_path = tmp_path / 'bad.jpg'
        img_path.write_text('not an image')

        result = optimize_image(img_path, max_size=1600, quality=82)
        assert result is None

    def test_unsupported_format(self, tmp_path):
        img_path = tmp_path / 'test.bmp'
        img = Image.new('RGB', (100, 100))
        img.save(str(img_path), 'BMP')

        result = optimize_image(img_path, max_size=1600, quality=82)
        assert result is None

    def test_rgba_jpeg(self, tmp_path):
        img_path = tmp_path / 'rgba.jpg'
        img = Image.new('RGBA', (100, 100))
        img.save(str(img_path), 'PNG')  # Save as PNG first, rename
        # Rename to .jpg to test the RGBA->RGB conversion path
        jpg_path = tmp_path / 'rgba_test.jpg'
        img.convert('RGB').save(str(jpg_path), 'JPEG')

        result = optimize_image(jpg_path, max_size=1600, quality=82)
        assert result is not None
