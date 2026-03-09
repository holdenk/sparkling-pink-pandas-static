"""Tests for scripts/assign_gallery_photos.py."""

from datetime import date

from assign_gallery_photos import add_image_to_front_matter, find_closest_photo


class TestFindClosestPhoto:
    def test_exact_match(self):
        photos = [
            ('/a.webp', date(2024, 6, 15)),
            ('/b.webp', date(2024, 7, 20)),
        ]
        result = find_closest_photo(date(2024, 6, 15), photos)
        assert result == ('/a.webp', date(2024, 6, 15))

    def test_closest(self):
        photos = [
            ('/a.webp', date(2024, 6, 10)),
            ('/b.webp', date(2024, 6, 20)),
        ]
        result = find_closest_photo(date(2024, 6, 18), photos)
        assert result == ('/b.webp', date(2024, 6, 20))

    def test_empty_list(self):
        assert find_closest_photo(date(2024, 6, 15), []) is None

    def test_single_photo(self):
        photos = [('/only.webp', date(2024, 1, 1))]
        result = find_closest_photo(date(2024, 12, 31), photos)
        assert result == ('/only.webp', date(2024, 1, 1))


class TestAddImageToFrontMatter:
    def test_basic(self):
        fm_raw = "\ntitle: Test\ndate: 2024-06-15\n"
        result = add_image_to_front_matter(fm_raw, '/assets/img/gallery/photo.webp')
        assert result.endswith('image: /assets/img/gallery/photo.webp\n')
        assert 'title: Test' in result

    def test_no_trailing_newline(self):
        fm_raw = "\ntitle: Test"
        result = add_image_to_front_matter(fm_raw, '/img/test.webp')
        assert 'image: /img/test.webp\n' in result
