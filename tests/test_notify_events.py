"""Tests for scripts/notify_events.py."""

from datetime import date, timedelta

from notify_events import build_email, find_pending_events
from conftest import write_event_file


class TestBuildEmail:
    def test_basic(self):
        meta = {'title': 'Ride Night', 'date': '2026-06-15',
                'time': '7:00 PM', 'location': 'Dolores Park',
                'description': 'A fun ride'}
        subject, text, html = build_email(meta, 'https://spp.com/events/2026/06/ride-night/',
                                          'https://spp.com')
        assert subject == 'New SPP Event: Ride Night'
        assert 'Ride Night' in text
        assert '7:00 PM' in text
        assert 'Dolores Park' in text
        assert 'https://spp.com/events/2026/06/ride-night/' in text
        assert '<h2>Ride Night</h2>' in html

    def test_minimal(self):
        meta = {'title': 'Test'}
        subject, text, html = build_email(meta, 'https://spp.com/events/2026/01/test/',
                                          'https://spp.com')
        assert subject == 'New SPP Event: Test'
        assert 'Time:' not in text
        assert 'Location:' not in text


class TestFindPendingEvents:
    def test_finds_pending(self, events_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        write_event_file(events_dir, f'{future}-test-event.md', {
            'title': 'Test',
            'date': future,
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 1

    def test_skips_already_emailed(self, events_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        write_event_file(events_dir, f'{future}-test.md', {
            'title': 'Test',
            'date': future,
            'emailed': '2026-01-01',
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 0

    def test_skips_past_events(self, events_dir):
        write_event_file(events_dir, '2020-01-01-old.md', {
            'title': 'Old',
            'date': '2020-01-01',
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 0

    def test_skips_non_md(self, events_dir):
        (events_dir / 'readme.txt').write_text('not an event')
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 0
