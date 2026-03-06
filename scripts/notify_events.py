#!/usr/bin/env python3
"""
Detect events that haven't been emailed yet and send notification emails.

Intended to run from GitHub Actions on push to main.

Environment variables:
    SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
    NOTIFY_FROM, NOTIFY_TO
    SITE_URL (default: https://sparklingpinkpandas.com)
    GITHUB_OUTPUT (set by GHA for step outputs)
"""

import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from utils import build_event_url, parse_event_file, update_event_frontmatter


def build_email(meta, event_url, site_url):
    """Build (subject, text_body, html_body) for an event notification."""
    title = meta.get('title', 'New Event')
    date = str(meta.get('date', ''))
    time_str = meta.get('time', '')
    location = meta.get('location', '')
    description = meta.get('description', '')

    subject = f"New SPP Event: {title}"

    text_body = f"""{title}
{'=' * len(title)}

Date: {date}"""
    if time_str:
        text_body += f"\nTime: {time_str}"
    if location:
        text_body += f"\nLocation: {location}"
    text_body += f"""

{description}

View event: {event_url}

--
Sparkling Pink Pandas
{site_url}
"""

    html_body = f"""<h2>{title}</h2>
<p><strong>Date:</strong> {date}</p>"""
    if time_str:
        html_body += f"<p><strong>Time:</strong> {time_str}</p>"
    if location:
        html_body += f"<p><strong>Location:</strong> {location}</p>"
    if description:
        html_body += f"<p>{description}</p>"
    html_body += f"""<hr>
<p><a href="{event_url}">View event on our website</a></p>
<hr>
<p><em>Sparkling Pink Pandas</em><br>
<a href="{site_url}">{site_url}</a></p>
"""
    return subject, text_body, html_body


def find_pending_events(events_dir, today):
    """Find events that need emailing: no 'emailed' field and date >= today."""
    pending = []
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.md'):
            continue
        filepath = os.path.join(events_dir, filename)
        result = parse_event_file(filepath)
        if result is None:
            continue
        meta, fm_raw, rest = result

        if meta.get('emailed'):
            continue
        event_date = meta.get('date')
        if not event_date:
            continue
        if hasattr(event_date, 'date'):
            event_date = event_date.date()
        if event_date < today:
            continue

        pending.append((filepath, filename, meta, fm_raw, rest))
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
        print("No events need emailing.")
        write_gha_output("updated", "false")
        return

    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = os.environ.get("SMTP_PORT", "")
    smtp_user = os.environ.get("SMTP_USERNAME", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    notify_from = os.environ.get("NOTIFY_FROM", "")
    notify_to = os.environ.get("NOTIFY_TO", "SparklingPinkPandas@googlegroups.com")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        print("SMTP credentials not configured, skipping email.")
        write_gha_output("updated", "false")
        return

    updated_any = False
    for filepath, filename, meta, fm_raw, rest in pending:
        event_url = build_event_url(filename, site_url)
        subject, text_body, html_body = build_email(meta, event_url, site_url)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = notify_from
        msg["To"] = notify_to
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(notify_from, [notify_to], msg.as_string())
            print(f"Email sent for event: {meta.get('title')}")
        except Exception as e:
            print(f"Error sending email for {meta.get('title')}: {e}")
            continue

        update_event_frontmatter(filepath, fm_raw, rest, {
            'emailed': today.isoformat(),
        })
        updated_any = True
        print(f"Marked {filename} as emailed.")

    write_gha_output("updated", "true" if updated_any else "false")


if __name__ == '__main__':
    main()
