"""Tests for scripts/add_event.py."""

from datetime import datetime
from unittest.mock import patch

from add_event import prompt, validate_date


class TestValidateDate:
    def test_valid_date(self):
        result = validate_date("2026-03-15")
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 15

    def test_invalid_format(self):
        assert validate_date("03-15-2026") is None

    def test_invalid_date(self):
        assert validate_date("2026-13-01") is None

    def test_empty(self):
        assert validate_date("") is None

    def test_garbage(self):
        assert validate_date("not-a-date") is None


class TestPrompt:
    def test_returns_input(self):
        with patch('builtins.input', return_value='hello'):
            assert prompt("Label") == 'hello'

    def test_returns_default_on_empty(self):
        with patch('builtins.input', return_value=''):
            assert prompt("Label", default='default_val') == 'default_val'

    def test_required_retries(self):
        with patch('builtins.input', side_effect=['', '', 'value']):
            assert prompt("Label", required=True) == 'value'

    def test_strips_whitespace(self):
        with patch('builtins.input', return_value='  hello  '):
            assert prompt("Label") == 'hello'
