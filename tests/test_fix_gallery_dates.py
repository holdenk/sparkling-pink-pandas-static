"""Tests for scripts/fix_gallery_dates.py."""

import json
from datetime import date

from fix_gallery_dates import find_json_sidecars, parse_takeout_date


class TestFindJsonSidecars:
    def test_standard_sidecar(self, tmp_path):
        album = tmp_path / 'Album1'
        album.mkdir()
        (album / 'IMG_1234.jpg').write_text('')
        (album / 'IMG_1234.jpg.json').write_text('{}')

        result = find_json_sidecars(str(tmp_path))
        assert 'img_1234.jpg' in result

    def test_duplicate_counter(self, tmp_path):
        album = tmp_path / 'Album1'
        album.mkdir()
        (album / 'IMG_1234.jpg(1).json').write_text('{}')

        result = find_json_sidecars(str(tmp_path))
        # Should have the reordered key: IMG_1234(1).jpg
        assert 'img_1234(1).jpg' in result

    def test_skips_metadata_json(self, tmp_path):
        (tmp_path / 'metadata.json').write_text('{}')
        result = find_json_sidecars(str(tmp_path))
        assert len(result) == 0

    def test_nested_dirs(self, tmp_path):
        nested = tmp_path / 'a' / 'b'
        nested.mkdir(parents=True)
        (nested / 'photo.jpg.json').write_text('{}')
        result = find_json_sidecars(str(tmp_path))
        assert 'photo.jpg' in result

    def test_empty_dir(self, tmp_path):
        result = find_json_sidecars(str(tmp_path))
        assert result == {}


class TestParseTakeoutDate:
    def test_valid_timestamp(self, tmp_path):
        data = {'photoTakenTime': {'timestamp': '1681567436'}}
        json_path = tmp_path / 'test.json'
        json_path.write_text(json.dumps(data))
        result = parse_takeout_date(str(json_path))
        assert isinstance(result, date)
        assert result.year == 2023

    def test_zero_timestamp(self, tmp_path):
        data = {'photoTakenTime': {'timestamp': '0'}}
        json_path = tmp_path / 'test.json'
        json_path.write_text(json.dumps(data))
        result = parse_takeout_date(str(json_path))
        assert result is None

    def test_missing_photo_taken_time(self, tmp_path):
        json_path = tmp_path / 'test.json'
        json_path.write_text('{"title": "test"}')
        result = parse_takeout_date(str(json_path))
        assert result is None

    def test_invalid_json(self, tmp_path):
        json_path = tmp_path / 'test.json'
        json_path.write_text('not json')
        result = parse_takeout_date(str(json_path))
        assert result is None

    def test_nonexistent_file(self, tmp_path):
        result = parse_takeout_date(str(tmp_path / 'nope.json'))
        assert result is None

    def test_empty_timestamp(self, tmp_path):
        data = {'photoTakenTime': {'timestamp': ''}}
        json_path = tmp_path / 'test.json'
        json_path.write_text(json.dumps(data))
        result = parse_takeout_date(str(json_path))
        assert result is None
