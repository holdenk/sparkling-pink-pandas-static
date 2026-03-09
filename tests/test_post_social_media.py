"""Tests for scripts/post_social_media.py."""

from datetime import date, timedelta

from post_social_media import build_post_text, find_pending_events
from conftest import write_event_file


class TestBuildPostText:
    def test_full(self):
        meta = {'title': 'Ride Night', 'date': '2026-06-15',
                'time': '7:00 PM', 'location': 'Dolores Park'}
        text = build_post_text(meta, 'https://spp.com/events/2026/06/ride-night/')
        assert 'New event: Ride Night' in text
        assert 'Date: 2026-06-15 at 7:00 PM' in text
        assert 'Location: Dolores Park' in text
        assert '#SparklingPinkPandas' in text

    def test_minimal(self):
        meta = {'title': 'Test'}
        text = build_post_text(meta, 'https://spp.com/events/2026/01/test/')
        assert 'New event: Test' in text
        assert 'Location:' not in text
        assert 'at ' not in text.split('Date:')[1].split('\n')[0]


class TestFindPendingEvents:
    def test_finds_events_needing_posts(self, events_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        write_event_file(events_dir, f'{future}-test.md', {
            'title': 'Test',
            'date': future,
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 1
        # Check needs_x, needs_bsky, needs_ig flags
        _, _, _, _, _, needs_x, needs_bsky, needs_ig = pending[0]
        assert needs_x is True
        assert needs_bsky is True
        assert needs_ig is True

    def test_skips_fully_posted(self, events_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        write_event_file(events_dir, f'{future}-done.md', {
            'title': 'Done',
            'date': future,
            'posted_x': 'https://x.com/123',
            'posted_bluesky': 'https://bsky.app/123',
            'posted_instagram': '456',
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 0

    def test_partially_posted(self, events_dir):
        future = (date.today() + timedelta(days=30)).isoformat()
        write_event_file(events_dir, f'{future}-partial.md', {
            'title': 'Partial',
            'date': future,
            'posted_x': 'https://x.com/123',
        })
        pending = find_pending_events(str(events_dir), date.today())
        assert len(pending) == 1
        _, _, _, _, _, needs_x, needs_bsky, needs_ig = pending[0]
        assert needs_x is False
        assert needs_bsky is True
        assert needs_ig is True
