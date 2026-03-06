"""Tests for scripts/sync_gallery.py."""


from sync_gallery import format_entry, get_exif_date, scan_photos

from datetime import date
from PIL import Image


class TestScanPhotos:
    def test_finds_images(self, repo_root):
        gallery = repo_root / 'assets' / 'img' / 'gallery'
        (gallery / 'a.jpg').write_text('')
        (gallery / 'b.webp').write_text('')
        (gallery / 'c.png').write_text('')
        (gallery / 'readme.txt').write_text('')

        result = scan_photos(str(gallery))
        assert result == ['a.jpg', 'b.webp', 'c.png']

    def test_empty_dir(self, repo_root):
        gallery = repo_root / 'assets' / 'img' / 'gallery'
        assert scan_photos(str(gallery)) == []

    def test_sorted(self, repo_root):
        gallery = repo_root / 'assets' / 'img' / 'gallery'
        (gallery / 'z.jpg').write_text('')
        (gallery / 'a.jpg').write_text('')
        result = scan_photos(str(gallery))
        assert result == ['a.jpg', 'z.jpg']


class TestFormatEntry:
    def test_with_date(self):
        result = format_entry('/assets/img/gallery/photo.webp', date(2024, 6, 15))
        assert result == '- image: /assets/img/gallery/photo.webp\n  date: 2024-06-15'

    def test_without_date(self):
        result = format_entry('/assets/img/gallery/photo.webp')
        assert result == '- image: /assets/img/gallery/photo.webp'


class TestGetExifDate:
    def test_no_exif(self, tmp_path):
        img_path = tmp_path / 'test.jpg'
        img = Image.new('RGB', (10, 10))
        img.save(str(img_path))
        result = get_exif_date(str(img_path))
        # Simple images typically have no EXIF date
        assert result is None

    def test_nonexistent_file(self, tmp_path):
        result = get_exif_date(str(tmp_path / 'nonexistent.jpg'))
        assert result is None
