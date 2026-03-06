#!/usr/bin/env python3
"""
Detect events that haven't been posted to social media and post them.

Intended to run from GitHub Actions on push to main.

Environment variables:
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
    BSKY_HANDLE, BSKY_PASSWORD
    IG_USERNAME, IG_PASSWORD
    SITE_URL (default: https://sparklingpinkpandas.com)
    GITHUB_OUTPUT (set by GHA for step outputs)
"""

import datetime
import os

from utils import build_event_url, parse_event_file, update_event_frontmatter


def build_post_text(meta, url):
    """Build a social media post from event metadata."""
    title = meta.get('title', 'New Event')
    date = str(meta.get('date', ''))
    time_str = meta.get('time', '')
    location = meta.get('location', '')

    lines = [f"New event: {title}"]
    date_line = f"Date: {date}"
    if time_str:
        date_line += f" at {time_str}"
    lines.append(date_line)
    if location:
        lines.append(f"Location: {location}")
    lines.append("")
    lines.append(url)
    lines.append("")
    lines.append("#SparklingPinkPandas #TransRiders #ScooterLife #SanFrancisco")
    return "\n".join(lines)


def post_to_x(text):
    """Post to X/Twitter. Returns tweet URL on success, None on failure."""
    api_key = os.environ.get("X_API_KEY")
    api_secret = os.environ.get("X_API_SECRET")
    access_token = os.environ.get("X_ACCESS_TOKEN")
    access_secret = os.environ.get("X_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        print("X/Twitter credentials not configured, skipping.")
        return None

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
        )
        response = client.create_tweet(text=text)
        tweet_id = response.data['id']
        print(f"Posted to X: {tweet_id}")
        return f"https://x.com/i/status/{tweet_id}"
    except Exception as e:
        print(f"Error posting to X: {e}")
        return None


def post_to_bluesky(text):
    """Post to Bluesky. Returns post URL on success, None on failure."""
    handle = os.environ.get("BSKY_HANDLE")
    password = os.environ.get("BSKY_PASSWORD")

    if not all([handle, password]):
        print("Bluesky credentials not configured, skipping.")
        return None

    try:
        from atproto import Client
        client = Client()
        client.login(handle, password)
        response = client.send_post(text=text)
        rkey = response.uri.split('/')[-1]
        url = f"https://bsky.app/profile/{handle}/post/{rkey}"
        print(f"Posted to Bluesky: {url}")
        return url
    except Exception as e:
        print(f"Error posting to Bluesky: {e}")
        return None


def post_to_instagram(text):
    """Post to Instagram. Returns media PK on success, None on failure."""
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")

    if not all([username, password]):
        print("Instagram credentials not configured, skipping.")
        return None

    try:
        from instagrapi import Client as IGClient
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        img = Image.new('RGB', (1080, 1080), color=(255, 77, 240))
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
        except Exception:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((540, 200), "Sparkling Pink Pandas",
                  fill="white", font=font_large, anchor="mm")
        draw.text((540, 280), "NEW EVENT",
                  fill="white", font=font_small, anchor="mm")

        wrapped = textwrap.fill(text.split("#")[0].strip(), width=35)
        y_pos = 400
        for line in wrapped.split("\n")[:10]:
            draw.text((540, y_pos), line, fill="white",
                      font=font_small, anchor="mm")
            y_pos += 45

        img_path = "/tmp/event_post.jpg"
        img.save(img_path)

        client = IGClient()
        client.login(username, password)
        media = client.photo_upload(img_path, caption=text)
        print(f"Posted to Instagram: {media.pk}")
        return str(media.pk)
    except Exception as e:
        print(f"Error posting to Instagram: {e}")
        return None


def find_pending_events(events_dir, today):
    """Find events needing social media posts: missing posted_* fields and date >= today."""
    pending = []
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(events_dir, filename)
        result = parse_event_file(filepath)
        if result is None:
            continue
        meta, fm_raw, rest = result

        event_date = meta.get('date')
        if not event_date:
            continue
        if hasattr(event_date, 'date'):
            event_date = event_date.date()
        if event_date < today:
            continue

        needs_x = not meta.get('posted_x')
        needs_bsky = not meta.get('posted_bluesky')
        needs_ig = not meta.get('posted_instagram')

        if not (needs_x or needs_bsky or needs_ig):
            continue

        pending.append((filepath, filename, meta, fm_raw, rest,
                         needs_x, needs_bsky, needs_ig))
    return pending


def write_gha_output(key, value):
    """Write a key=value pair to GITHUB_OUTPUT if available."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"{key}={value}\n")


def main():
    events_dir = '_events'
    site_url = os.environ.get("SITE_URL", "https://sparklingpinkpandas.com")
    today = datetime.date.today()

    pending = find_pending_events(events_dir, today)

    if not pending:
        print("No events need posting.")
        write_gha_output("updated", "false")
        return

    updated_any = False
    for filepath, filename, meta, fm_raw, rest, needs_x, needs_bsky, needs_ig in pending:
        url = build_event_url(filename, site_url)
        text = build_post_text(meta, url)
        print(f"--- Processing: {meta.get('title')} ---")
        print(text)
        print("---")

        new_fields = {}

        if needs_x:
            result = post_to_x(text)
            if result:
                new_fields['posted_x'] = result

        if needs_bsky:
            result = post_to_bluesky(text)
            if result:
                new_fields['posted_bluesky'] = result

        if needs_ig:
            result = post_to_instagram(text)
            if result:
                new_fields['posted_instagram'] = result

        if new_fields:
            update_event_frontmatter(filepath, fm_raw, rest, new_fields)
            updated_any = True
            print(f"Updated {filename} with: {', '.join(new_fields.keys())}")

    write_gha_output("updated", "true" if updated_any else "false")


if __name__ == '__main__':
    main()
