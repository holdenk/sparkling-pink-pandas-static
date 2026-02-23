#!/usr/bin/env python3
"""
Add a new event to the Sparkling Pink Pandas website.

Creates a properly formatted markdown file in the _events/ directory.

Usage:
    python3 scripts/add_event.py [--no-notify]

Options:
    --no-notify  Skip automated notifications (email, social media) for this
                 event. Use for backdated or historical events that shouldn't
                 trigger announcements.

You'll be prompted for:
  - Title (required)
  - Date (required, YYYY-MM-DD)
  - Time (optional, e.g. "2:00 PM")
  - Location (optional)
  - Description (required)
  - Image path (optional, relative to site root)
  - Map URL (optional, e.g. Google Maps link)

The script generates a file like:
    _events/2026-03-01-my-event-title.md

Tracking fields (emailed, posted_x, posted_bluesky, posted_instagram) are
intentionally omitted from new events. Their absence signals to the GitHub
Actions workflows that the event needs to be announced. Use --no-notify to
pre-populate these fields with "skip" and prevent notifications.
"""

import os
import re
import sys
from datetime import datetime


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def prompt(label, required=False, default=None):
    """Prompt user for input with optional default."""
    suffix = f" [{default}]" if default else ""
    marker = " (required)" if required else ""
    while True:
        value = input(f"{label}{marker}{suffix}: ").strip()
        if not value and default:
            return default
        if not value and required:
            print(f"  {label} is required, please enter a value.")
            continue
        return value


def validate_date(date_str):
    """Validate and parse a date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None


def main():
    no_notify = '--no-notify' in sys.argv
    print()
    print("=== Add New Event to Sparkling Pink Pandas ===")
    if no_notify:
        print("  (--no-notify: this event will NOT trigger notifications)")
    print()

    # Title
    title = prompt("Event title", required=True)

    # Date
    while True:
        date_str = prompt("Date (YYYY-MM-DD)", required=True,
                          default=datetime.now().strftime("%Y-%m-%d"))
        dt = validate_date(date_str)
        if dt:
            break
        print("  Invalid date format. Use YYYY-MM-DD (e.g. 2026-03-01)")

    # Time
    time_str = prompt("Time (e.g. '2:00 PM')")

    # Location
    location = prompt("Location")

    # Description (short, for listings)
    description = prompt("Short description (for event listings)", required=True)

    # Image
    print()
    print("  Images should be in assets/img/gallery/ or assets/img/")
    print("  Example: /assets/img/gallery/my-photo.jpg")
    image = prompt("Image path (leave blank for default)")

    # Map URL
    map_url = prompt("Map/route URL (leave blank to skip)")

    # Body content
    print()
    print("Enter the full event description (press Enter twice to finish):")
    body_lines = []
    empty_count = 0
    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
            body_lines.append("")
        else:
            empty_count = 0
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    if not body:
        body = description

    # Build the filename
    slug = slugify(title)
    filename = f"{date_str}-{slug}.md"
    filepath = os.path.join("_events", filename)

    # Check for existing file
    if os.path.exists(filepath):
        overwrite = input(f"\n  {filepath} already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("  Cancelled.")
            sys.exit(0)

    # Build front matter
    front_matter = ['---']
    front_matter.append(f'title: "{title}"')
    front_matter.append(f'date: {date_str}')
    if time_str:
        front_matter.append(f'time: "{time_str}"')
    if location:
        front_matter.append(f'location: "{location}"')
    front_matter.append(f'description: "{description}"')
    if image:
        front_matter.append(f'image: {image}')
    if map_url:
        front_matter.append(f'map_url: "{map_url}"')
    if no_notify:
        front_matter.append('emailed: "skip"')
        front_matter.append('posted_x: "skip"')
        front_matter.append('posted_bluesky: "skip"')
        front_matter.append('posted_instagram: "skip"')
    front_matter.append('---')

    content = "\n".join(front_matter) + "\n\n" + body + "\n"

    # Write the file
    os.makedirs("_events", exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)

    print()
    print(f"  Event created: {filepath}")
    print()
    print(f"  URL will be: /events/{dt.year}/{dt.month:02d}/{slug}/")
    print()
    print("  Next steps:")
    print(f"    1. Review the file: cat {filepath}")
    print(f"    2. Build locally:   bundle exec jekyll serve")
    print(f"    3. Commit:          git add {filepath} && git commit -m 'Add event: {title}'")
    print(f"    4. Push:            git push")
    print()


if __name__ == "__main__":
    main()
