# Sparkling Pink Pandas Website

Static website for the Sparkling Pink Pandas, a queer and trans-focused scooter and motorcycle group in San Francisco.

Built with Jekyll and deployed to GitHub Pages.

## Quick Start

### Prerequisites

- Ruby 3.x
- Bundler (`gem install bundler`)
- Git LFS (`git lfs install`)

### Local Development

```bash
git clone <repo-url>
cd sparklingpinkpandas-static-web
git lfs pull              # download large media files
bundle install            # install Ruby dependencies
bundle exec jekyll serve  # start local server at http://localhost:4000
```

## Adding Content

### Add an Event

The easiest way is to use the helper script:

```bash
python3 scripts/add_event.py
```

It will prompt you for the event details and create the markdown file.

To add an event manually, create a file in `_events/` named `YYYY-MM-DD-event-slug.md`:

The "slug" will end up being part of the URL so if we have two events on the same day pick a different slug :p

```markdown
---
title: "My Event Title"
date: 2026-04-15
time: "2:00 PM"
location: "San Francisco, CA"
description: "Short description for event listings."
image: /assets/img/gallery/some-photo.jpg
map_url: "https://maps.google.com/..."
---

Full event description goes here. Markdown is supported.
```

The event will appear at `/events/YYYY/MM/event-slug/`.

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Event name |
| `date` | Yes | Date in YYYY-MM-DD format |
| `time` | No | Display time (e.g. "2:00 PM") |
| `location` | No | Where the event takes place |
| `description` | Yes | Short text for listings |
| `image` | No | Path to event image |
| `map_url` | No | Link to a route map |

### Add a Blog Post

Create a file in `_posts/` named `YYYY-MM-DD-post-title.md`:

```markdown
---
title: "Post Title"
author: "Your Name"
image: /assets/img/gallery/photo.jpg
---

Post content in markdown.
```

### Add Photos to the Gallery

1. Place images in `assets/img/gallery/`
2. Add an entry to `_data/gallery.yml`:

```yaml
- image: /assets/img/gallery/my-photo.jpg
  caption: "Description of the photo"
  date: 2026-01-15
  credit_name: Photographer Name
  credit_url: https://photographer-website.com
  instagram_url: https://www.instagram.com/sparklingpinkpandas/
```

All fields except `image` are optional.

### Add Videos

For YouTube videos, add the embed to `gallery.html` in the video section.

To store video files, place them in `assets/video/`. They are tracked via git LFS.

### Edit Social Links

Edit `_data/social.yml` to add or change social media links:

```yaml
- name: Instagram
  url: https://www.instagram.com/sparklingpinkpandas/
  icon: fab fa-instagram
```

Icons use [FontAwesome 5](https://fontawesome.com/v5/search) class names.

## Project Structure

```
_config.yml           # Jekyll configuration
_data/
  gallery.yml         # Gallery photo entries
  social.yml          # Social media links
_events/              # Event pages (markdown)
_posts/               # Blog posts (markdown)
_layouts/             # Page templates
  default.html        # Base layout (head, header, footer, scripts)
  event.html          # Single event page
  page.html           # Generic page (about, etc.)
  post.html           # Blog post page
_includes/            # Reusable template fragments
  header.html         # Site header and navigation
  footer.html         # Site footer
  event-card.html     # Event card for listings
  post-card.html      # Blog post card for listings
assets/
  css/site.css        # Custom styles (all other CSS is vendor)
  js/main.js          # Mobile menu toggle + lightbox init
  img/                # Site images
  img/gallery/        # Gallery photos (git LFS)
  video/              # Video files (git LFS)
scripts/
  add_event.py        # Helper script to create events
index.html            # Homepage
events.html           # Events listing (upcoming + past)
blog.html             # Blog listing
gallery.html          # Photo gallery + YouTube videos
about.md              # About page with mission, FAQ, press
events.ics            # iCal feed (auto-generated from events)
```

## Deployment

The site auto-deploys to GitHub Pages on push to `main` via GitHub Actions. When a new event is added, two additional workflows automatically send email notifications and post to social media.

### GitHub Actions Workflows

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `jekyll.yml` | Every push to `main` | Builds the Jekyll site and deploys to GitHub Pages |
| `notify-new-event.yml` | New `.md` file added to `_events/` | Sends an email to the Google Group |
| `post-social-media.yml` | New `.md` file added to `_events/` | Posts to X, Bluesky, and Instagram |

### GitHub Pages Setup

1. Go to **Settings > Pages**
2. Under **Build and deployment > Source**, select **GitHub Actions**
3. Go to **Settings > Environments** and confirm a `github-pages` environment exists (created automatically after the first deploy)

#### Required Permissions

The `jekyll.yml` workflow needs these token permissions (already configured in the workflow file):

| Permission | Level | Why |
|------------|-------|-----|
| `contents` | `read` | Read repo to build the site |
| `pages` | `write` | Deploy to GitHub Pages |
| `id-token` | `write` | OIDC token for Pages deployment |

If your repository uses restricted default permissions, go to **Settings > Actions > General > Workflow permissions** and ensure **Read repository contents** is enabled. The `pages` and `id-token` permissions are granted per-workflow in the YAML files.

### Notification Setup

The notification workflows (`notify-new-event.yml` and `post-social-media.yml`) only need `contents: read` permission, which is the default. They use repository secrets for credentials to external services.

All notification secrets are optional -- each platform is skipped gracefully if its credentials are missing. You can enable just the ones you need.

#### Adding Secrets

1. Go to **Settings > Secrets and variables > Actions**
2. Click **New repository secret**
3. Add each secret by name and value

#### Email Notifications (Google Group)

| Secret | Description |
|--------|-------------|
| `SMTP_HOST` | SMTP server hostname (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (typically `587` for STARTTLS) |
| `SMTP_USERNAME` | Email address to send from |
| `SMTP_PASSWORD` | SMTP password or app password |

**Gmail setup:** Use `smtp.gmail.com` port `587`. You must generate an [App Password](https://myaccount.google.com/apppasswords) (requires 2FA enabled on the account). Use the app password as `SMTP_PASSWORD`, not your regular Gmail password.

Emails are sent to `SparklingPinkPandas@groups.google.com`. To change the recipient, edit `NOTIFY_TO` in `notify-new-event.yml`.

#### X / Twitter

| Secret | Description |
|--------|-------------|
| `X_API_KEY` | API key (consumer key) |
| `X_API_SECRET` | API secret (consumer secret) |
| `X_ACCESS_TOKEN` | Access token |
| `X_ACCESS_SECRET` | Access token secret |

**Setup:** Create a project and app at [developer.x.com](https://developer.x.com). Under your app's **Keys and tokens**, generate all four values. The app needs **Read and Write** permissions.

#### Bluesky

| Secret | Description |
|--------|-------------|
| `BSKY_HANDLE` | Your handle (e.g. `sparklingpinkpandas.bsky.social`) |
| `BSKY_PASSWORD` | App password |

**Setup:** In the Bluesky app, go to **Settings > App Passwords** and create a new app password. Use that as `BSKY_PASSWORD` (not your account password).

#### Instagram

| Secret | Description |
|--------|-------------|
| `IG_USERNAME` | Instagram username |
| `IG_PASSWORD` | Instagram password |

**Note:** Instagram automation uses the unofficial `instagrapi` library. Instagram may challenge logins from new IPs (like GitHub Actions runners). This is the least reliable of the three platforms. If it stops working, the other platforms are unaffected.

#### Optional Variables

Variables are set under **Settings > Secrets and variables > Actions > Variables** tab.

| Variable | Default | Description |
|----------|---------|-------------|
| `SITE_URL` | `https://sparklingpinkpandas.com` | Base URL used in notification links |

## Git LFS

Large files (images, videos) are tracked with git LFS. After cloning, run:

```bash
git lfs pull
```

Tracked extensions: jpg, jpeg, png, gif, webp, svg, bmp, tiff, tif, heic, heif, avif, ico, mp4, mov, avi, webm, mkv

## Tech Stack

- **Jekyll 4.3** - Static site generator
- **Bootstrap 4** - CSS framework
- **FontAwesome 5** - Icons
- **Magnific Popup** - Lightbox for gallery images
- **Google Fonts** - Roboto + Maven Pro
