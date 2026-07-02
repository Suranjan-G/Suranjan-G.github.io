# suranjangoswami.com

Personal website. Plain HTML + CSS, generated from text sources by a single Python script (`sync.py`). No third-party dependencies. Hosted on GitHub Pages.

## Contents

- [Structure](#structure)
- [Quick start](#quick-start)
- [Edit any page](#edit-any-page) — page-by-page reference
  - [Home page (`/`)](#home-page-)
  - [About page (`/about/`)](#about-page-about)
  - [Experience page (`/experience/`)](#experience-page-experience)
  - [Publications page (`/publications/`)](#publications-page-publications)
  - [Talks / Judging page (`/talks/`)](#talks--judging-page-talks)
  - [Site-wide elements (nav, footer, styles)](#site-wide-elements-nav-footer-styles)
  - [Social preview image (Open Graph)](#social-preview-image-open-graph)
- [Inline formatting reference](#inline-formatting-reference)
- [Adding a new content block](#adding-a-new-content-block)
- [Media — talk images and videos (Cloudinary-hosted)](#media--talk-images-and-videos-cloudinary-hosted)
  - [One-time setup](#one-time-setup)
  - [What to install + what to keep on disk](#what-to-install--what-to-keep-on-disk)
  - [Adding new media](#adding-new-media)
- [Local preview](#local-preview)
- [Deploy to GitHub Pages](#deploy-to-github-pages)
- [Alternative: host on `<username>.github.io` without a custom domain](#alternative-host-on-usernamegithubio-without-a-custom-domain)
- [Extending the pipeline (new page / new section)](#extending-the-pipeline-new-page--new-section)

---

## Structure

```
.
├── sync.py                        # Build script — regenerates every HTML page
├── content/                       # ✎  Source of truth (edit these)
│   ├── profile.txt                # Name, tagline, bio, contact, home hero
│   ├── experience.txt             # Work history (jobs + nested sub-bullets)
│   ├── publications.txt           # Highlighted + regular papers + datasets
│   ├── education.txt              # Degrees
│   ├── awards.txt                 # Awards, certificates, hobbies
│   ├── skills.txt                 # Skill tag groups
│   └── projects.txt               # Selected projects list
├── talks/
│   ├── details.txt                # ✎  Talks/judging source (colocated w/ media)
│   ├── images+videos/             # ✎  Local staging area for originals (gitignored)
│   │   ├── manifest.json          # ⚙  Filename → Cloudinary public_id map (committed)
│   │   └── *.JPG / *.mp4 / ...    # ✎  Local originals (gitignored, live on Cloudinary)
│   └── index.html                 # ⚙  Generated — do NOT edit by hand
├── styles.css                     # ✎  All CSS (single file)
├── index.html                     # ⚙  Generated
├── about/index.html               # ⚙  Generated
├── experience/index.html          # ⚙  Generated
├── publications/index.html        # ⚙  Generated
├── CNAME                          # Custom domain — do not delete
├── robots.txt
├── .gitignore
├── .cloudinary.example            # ✎  Template for the (gitignored) `.cloudinary` credentials file
└── README.md
```

**Legend:** ✎ = edit these · ⚙ = generated, do not edit by hand

## Quick start

Every content change is three steps:

```bash
# 1. Edit the relevant source file (see "Edit any page" below for what maps to what)

# 2. Rebuild every HTML page
python3 sync.py

# 3. Preview locally (if server not already running)
python3 -m http.server 8000
# open http://localhost:8000 — hard-refresh (Cmd+Shift+R) to bypass cache
```

**`sync.py` is idempotent** — running it twice is safe. It only rewrites files whose output would change. Add `--check` to make it exit 1 if any output would change (useful as a pre-commit or CI hook).

---

## Edit any page

Every visible element on every page maps to a field in a source file. The tables below cover **every element** shown on the site.

### Home page (`/`)

Rendered layout, top → bottom:

1. Nav bar
2. Name (large heading)
3. Tagline (subtitle under name)
4. Intro paragraph
5. "Recent" paragraph (with yellow highlight)
6. Contact links row (email · LinkedIn · Scholar · IEEE Dataport)
7. Section: "Selected highlights" — bulleted list
8. Section: "Research interests" — pill-shaped skill tags
9. Footer

**All Home-page content lives in `content/profile.txt`.**

| Visible element                            | Field in `content/profile.txt` |
|--------------------------------------------|--------------------------------|
| Browser tab title                          | `home_title:`                  |
| SEO / social-share description             | `home_description:`            |
| Name (h1)                                  | `name:`                        |
| Tagline (subtitle)                         | `tagline:`                     |
| First paragraph under name                 | `hero_intro:`                  |
| Second paragraph (with yellow highlight)   | `hero_recent:`                 |
| Email in contact row                       | `email:`                       |
| LinkedIn URL                               | `linkedin:`                    |
| Google Scholar URL                         | `scholar:`                     |
| IEEE Dataport URL                          | `dataport:`                    |
| "Selected highlights" bullets              | `highlights:` (list)           |
| "Research interests" pill tags             | `interests:` (list)            |

**Example — change your current role from Nasiko to a new company:**

Edit `hero_intro:` in `content/profile.txt`:
```
hero_intro: Research Scientist at <NEW COMPANY>, working on ...
```

**Example — add another highlight:**

Under the `highlights:` field, add an indented `- ` line:
```
highlights:
  - **A* publication, ICLR 2026** — _IndicVisionBench_, ...
  - **New highlight** — description here with _emphasis_.
  - ...existing bullets...
```

Then `python3 sync.py`.

---

### About page (`/about/`)

Rendered layout, top → bottom:

1. Nav
2. H1: "About"
3. Lead paragraph (under H1)
4. Section: "Summary" — one paragraph
5. Section: "Trajectory" — three paragraphs (one per career phase)
6. Section: "Education" — degree entries
7. Section: "Awards & recognition" — bulleted list (optional badge)
8. Section: "Certificates & training" — bulleted list
9. Section: "Beyond research" — hobbies line
10. Footer

**About-page content comes from THREE files** (each covers a different section):

| Visible element                            | File → Field                                          |
|--------------------------------------------|-------------------------------------------------------|
| Browser tab title                          | Auto: `About — {name from profile.txt}`               |
| SEO description                            | `content/profile.txt` → `about_description:`          |
| Lead paragraph (under H1)                  | `content/profile.txt` → `about_lead:`                 |
| "Summary" paragraph                        | `content/profile.txt` → `about_summary:`              |
| "Trajectory" — each paragraph              | `content/profile.txt` → `about_trajectory:` (list)    |
| "Education" — each degree entry            | `content/education.txt` → one `---` block per degree  |
| "Awards & recognition" — each item         | `content/awards.txt` → `awards:` (list)               |
| "Certificates & training" — each item      | `content/awards.txt` → `certificates:` (list)         |
| "Beyond research" — hobbies line           | `content/awards.txt` → `hobbies:`                     |

**Example — add a new degree:**

Edit `content/education.txt` and add a new `---` block (order in file = order on page):
```
---
degree: Postdoc, Some Field
dates: 09/2027
institution: **Some University** — City
```

**Example — add an award with a colored badge:**

Edit `content/awards.txt`. Prefix the bullet with `!TAG ` — TAG becomes a solid navy badge:
```
awards:
  - !A* Publication at ICLR 2026
  - !NEW! Some new recognition — organization
  - Young Alumnus Award 2024 — IEM Kolkata
```

`!A*`, `!NEW!`, or any non-space token you prefix with `!` renders as a badge.

---

### Experience page (`/experience/`)

Rendered layout, top → bottom:

1. Nav
2. H1: "Experience"
3. Lead paragraph
4. Section: "Work history" — one card per job (title, dates, org, bullets)
5. Section: "Selected projects" — bulleted list
6. Section: "Skills" — three groups (Domains / Tools & platforms / Hardware & instrumentation)
7. Footer

| Visible element                            | File → Field                                          |
|--------------------------------------------|-------------------------------------------------------|
| Browser tab title                          | Auto: `Experience — {name from profile.txt}`          |
| SEO description                            | `content/profile.txt` → `experience_description:`     |
| Lead paragraph                             | `content/profile.txt` → `experience_lead:`            |
| Each job card                              | `content/experience.txt` → one `---` block per job    |
| Job title                                  | `content/experience.txt` → `title:`                   |
| Employer name                              | `content/experience.txt` → `org:`                     |
| Date range                                 | `content/experience.txt` → `dates:`                   |
| Bulleted responsibilities                  | `content/experience.txt` → `bullets:` (list)          |
| Nested sub-bullets under the LAST bullet   | `content/experience.txt` → `sub_bullets:` (list)      |
| "Selected projects" bullets                | `content/projects.txt` → `items:` (list)              |
| Skills group heading                       | `content/skills.txt` → `heading:` (per block)         |
| Skill tag pills within a group             | `content/skills.txt` → `tags:` (list, per block)      |

**Example — add a new current job (Nasiko → NewCo):**

Edit `content/experience.txt`. Add a new `---` block at the **top** (top of file = most recent):
```
---
title: Staff Research Scientist
org: NewCo
dates: 08/2026 – Present
bullets:
  - Led something important
  - Shipped some project
  - Managed team of X
```

Then update the current Nasiko entry to end its date range (e.g. `04/2026 – 07/2026`).

**Example — add sub-bullets under a job's last bullet:**

Add a `sub_bullets:` list after `bullets:`. It renders as a nested `<ul>` under the last main bullet:
```
title: Senior Research Engineer
org: Ola Electric
dates: 11/2023 – 03/2026
bullets:
  - Some responsibility
  - Another responsibility
  - Vision pipeline for factory automation
sub_bullets:
  - Sub-detail 1
  - Sub-detail 2
```

**Example — add a new skill group:**

Edit `content/skills.txt`, add a new `---` block:
```
---
heading: Cloud & DevOps
tags:
  - AWS
  - Docker
  - Kubernetes
```

---

### Publications page (`/publications/`)

Rendered layout, top → bottom:

1. Nav
2. H1: "Publications"
3. Lead paragraph (with a Google Scholar link)
4. Section: "Highlighted" — card-style entries with 2 badges each
5. Section: "Journal & conference papers" — plain entries
6. Section: "Open datasets" — plain entries
7. Footer

| Visible element                            | File → Field                                                  |
|--------------------------------------------|---------------------------------------------------------------|
| Browser tab title                          | Auto: `Publications — {name}`                                 |
| SEO description                            | `content/profile.txt` → `publications_description:`           |
| Lead paragraph (with Scholar link)         | `content/profile.txt` → `publications_lead:`                  |
| Every entry (any section)                  | `content/publications.txt` → one `---` block per entry        |
| Solid navy badge on a highlight            | `content/publications.txt` → `primary_badge:` (highlights only) |
| Outlined muted badge on a highlight        | `content/publications.txt` → `muted_badge:` (highlights only) |
| Which section an entry lands in            | `content/publications.txt` → `type:` = `highlight`/`paper`/`dataset` |
| Title                                      | `content/publications.txt` → `title:`                         |
| Citation line (venue, year, DOI, etc.)     | `content/publications.txt` → `citation:`                      |

**Example — add a new paper:**

Edit `content/publications.txt`, add a `---` block. `type: paper` puts it in "Journal & conference papers":
```
---
type: paper
title: My new paper title
citation: Goswami, Suranjan et al. _Venue Name_ 42 (2027): 1234–1245. (IF: X.Y)
```

**Example — promote a paper to "Highlighted" with badges:**

Change `type:` to `highlight` and add both badge fields:
```
---
type: highlight
primary_badge: A*
muted_badge: NeurIPS 2027
title: A new hot paper
citation: Goswami, Suranjan et al. _NeurIPS_, 2027.
```

**Example — add a dataset with a clickable DOI:**

`type: dataset` sends it to the "Open datasets" section. Use `[text](url)` markdown for the DOI link inside the citation:
```
---
type: dataset
title: Some new dataset
citation: Goswami, Suranjan. IEEE Dataport, 2027. doi: [10.21227/xyz-1234](https://dx.doi.org/10.21227/xyz-1234)
```

---

### Talks / Judging page (`/talks/`)

Rendered layout, top → bottom:

1. Nav
2. H1: "Talks / Judging"
3. Lead paragraph
4. Grid of talk/judging cards, each with:
   - Colored badge (TALK = navy, JUDGING = amber)
   - Image / video carousel (swipe on mobile, arrows on hover on desktop, "1 / N" counter)
   - Title
   - Venue · Date line
   - Description
   - Optional links row (Slides / Video / Event page)
5. Footer

| Visible element                            | File → Field                                                    |
|--------------------------------------------|-----------------------------------------------------------------|
| Browser tab title                          | Auto: `Talks / Judging — {name}`                                |
| SEO description                            | `content/profile.txt` → `talks_description:`                    |
| Lead paragraph                             | `content/profile.txt` → `talks_lead:`                           |
| Each card                                  | `talks/details.txt` → one `---` block per card                  |
| TALK vs JUDGING badge                      | `talks/details.txt` → `type:` = `talk` or `judge`               |
| Card title                                 | `talks/details.txt` → `title:`                                  |
| Venue (event + city/country)               | `talks/details.txt` → `venue:`                                  |
| Date after the `·`                         | `talks/details.txt` → `date:` (any format, shown verbatim)      |
| Description paragraph                      | `talks/details.txt` → `description:`                            |
| Carousel of images/videos                  | `talks/details.txt` → `media:` (comma-separated filenames)      |
| "Slides" link                              | `talks/details.txt` → `slides:`                                 |
| "Video" link                               | `talks/details.txt` → `video:`                                  |
| "Event page" link                          | `talks/details.txt` → `event:`                                  |

**Rules for `media:`:**
- Comma-separated list of filenames living in `talks/images+videos/`
- Extension controls render: `.jpg`, `.png`, `.webp` → `<img>` · `.mp4`, `.webm`, `.mov` → `<video>` with native controls
- One file = single hero image, no carousel controls
- Two or more = carousel with dots, "N / M" counter, arrows on desktop hover, native swipe on mobile

**Example — add a new talk with 3 photos and a video clip:**

1. Drop the media into `talks/images+videos/`:
   ```
   talks/images+videos/talk-neurips-1.jpg
   talks/images+videos/talk-neurips-2.jpg
   talks/images+videos/talk-neurips-3.jpg
   talks/images+videos/talk-neurips-clip.mp4
   ```

2. Add a `---` block at the top of `talks/details.txt` (top = shown first):
   ```
   ---
   type: talk
   title: Title of the talk
   venue: NeurIPS Workshop, City, Country
   date: 2027-12-08
   description: 1–3 line description of what the talk covered.
   media: talk-neurips-1.jpg, talk-neurips-2.jpg, talk-neurips-3.jpg, talk-neurips-clip.mp4
   slides: https://example.com/slides.pdf
   video:
   event: https://neurips.cc/workshop-xyz
   ```

3. Run `python3 sync.py`.

**Example — change a card from Talk to Judging (or vice versa):**

Change `type: talk` → `type: judge` (or the other way). Badge and color flip automatically.

**Example — reorder cards:**

The order of `---` blocks in `talks/details.txt` = the order on the page (top of file = first card).

---

### Site-wide elements (nav, footer, styles)

Some elements are shared across every page.

| Visible element                        | Where to change                            |
|----------------------------------------|--------------------------------------------|
| "Suranjan Goswami" brand in nav        | `content/profile.txt` → `name:`            |
| Copyright line in footer               | Same — auto-uses `name:`                   |
| Footer links (Email/LinkedIn/…)        | `content/profile.txt` → `email:`, `linkedin:`, `scholar:`, `dataport:` |
| Nav labels ("Home", "About", …)        | `sync.py` → `NAV_ITEMS` list near the top  |
| Nav order                              | `sync.py` → `NAV_ITEMS` list               |
| Colors, spacing, layout                | `styles.css` — CSS variables at the top    |
| Accent color (navy)                    | `styles.css` → `--accent: #1e4d6f;`        |
| "TALK" badge color                     | `styles.css` → `.talk-card .type-tag.talk` |
| "JUDGING" badge color                  | `styles.css` → `.talk-card .type-tag.judge` (currently `#b8703a` amber) |
| Social preview image (LinkedIn/X/Slack) | `sync.py` → `CLOUDINARY_OG_IMAGE_PUBLIC_ID` — see [Social preview image](#social-preview-image-open-graph) below |
| Social preview crop / dimensions       | `sync.py` → `CLOUDINARY_OG_IMAGE_TRANSFORM` |

**Note:** `styles.css` is **not** generated by `sync.py`. Edit it directly — changes apply immediately, no sync needed.

### Social preview image (Open Graph)

When someone shares any URL from your site — on LinkedIn, Twitter/X, Slack, iMessage, WhatsApp, in a search-engine result card — those platforms read the page's `<meta property="og:*">` tags and generate a preview card. `sync.py` embeds a complete set of Open Graph + Twitter Card tags on every page, all pointing at a single "hero" image hosted on Cloudinary.

**What's set on every page:**

- `og:title`, `og:description` — per-page (matches the browser tab title + meta description)
- `og:url` — the canonical URL of the page
- `og:image` — a Cloudinary-transformed variant of your chosen source image, sized to **1200 × 630 px** (Facebook / LinkedIn recommended, ~1.91:1)
- `og:image:alt` — auto-built from `name:` + `tagline:` in `content/profile.txt`
- Twitter card variants: `twitter:card=summary_large_image`, `twitter:image`, etc.

**To change the source image:**

1. Make sure the image exists in `talks/images+videos/` and has been uploaded (`python3 sync.py --upload`).
2. In `sync.py`, edit `CLOUDINARY_OG_IMAGE_PUBLIC_ID` (near the top, under Cloudinary configuration):
   ```python
   CLOUDINARY_OG_IMAGE_PUBLIC_ID = "talks/DSC00948"   # ← whatever public_id you want
   ```
   The `public_id` is `talks/<basename-without-extension>` — check `talks/images+videos/manifest.json` for the exact value.
3. `python3 sync.py` — rewrites every page's OG tags.
4. Commit + push.

**To change the crop / dimensions:**

Edit `CLOUDINARY_OG_IMAGE_TRANSFORM`:

```python
CLOUDINARY_OG_IMAGE_TRANSFORM = "w_1200,h_630,c_fill,g_auto,f_auto,q_auto"
```

Common variations:

| Transform                                          | Effect                              |
|----------------------------------------------------|-------------------------------------|
| `w_1200,h_630,c_fill,g_auto,f_auto,q_auto`         | Default — smart crop to 1200×630   |
| `w_1200,h_630,c_fill,g_face,f_auto,q_auto`         | Center on detected face             |
| `w_1200,h_630,c_fill,g_center,f_auto,q_auto`       | Exact-center crop (no auto-detect) |
| `w_1200,h_630,c_fill,g_north,f_auto,q_auto`        | Anchor to top of image             |
| `w_1200,h_630,c_pad,b_auto,f_auto,q_auto`          | Pad with background instead of crop |
| `w_1200,h_1200,c_fill,g_auto,f_auto,q_auto`        | Square 1200×1200 (some chat apps) |

Full Cloudinary transformation reference: https://cloudinary.com/documentation/transformation_reference

**To preview what the OG image will actually look like:**

Paste the exact `og:image` URL from any generated HTML into your browser. Or construct it directly:

```
https://res.cloudinary.com/<cloud_name>/image/upload/<transform>/<public_id>
```

Example (current setup):
```
https://res.cloudinary.com/wbtgpw3v/image/upload/w_1200,h_630,c_fill,g_auto,f_auto,q_auto/talks/DSC00948
```

**Forcing platforms to refresh their cached preview:**

LinkedIn, Facebook, Twitter/X, and others cache OG previews aggressively — sometimes for weeks. After you change the image and push, use these tools to force a re-fetch:

- **LinkedIn:** https://www.linkedin.com/post-inspector/ → paste URL → "Fetch new data"
- **Facebook / Meta:** https://developers.facebook.com/tools/debug/ → paste URL → "Scrape Again"
- **Twitter / X:** https://cards-dev.twitter.com/validator (deprecated but still functional in some regions)
- **iMessage / Slack:** typically re-fetch every ~24 hours, no manual control

Do this *before* sharing the URL publicly — that way the first person to see it already sees the correct preview.

**Design tip:** the OG image is displayed at ~600×315 px in most feeds. Detail below ~40 px tall is essentially invisible. If your source image has small text or a face in the corner, use `g_face` or `g_center` so the important element ends up in the middle after cropping.

---

## Inline formatting reference

The following syntax works inside **any** text field (title, description, bullet, paragraph, etc.). Everything else is HTML-escaped so you can't accidentally inject broken HTML.

| Syntax                        | Renders as                                     |
|-------------------------------|------------------------------------------------|
| `**bold text**`               | **bold text**                                  |
| `_italic text_`               | _italic text_                                  |
| `==highlighted text==`        | yellow-marker span (matches CV theme)          |
| `[link text](https://example.com)` | [link text](https://example.com)          |

**Notes:**
- Underscores inside words (`file_name`) are NOT treated as italic — only underscores at word boundaries.
- If you really need raw HTML in a field, it will be escaped and appear as text — instead, use the markdown-lite syntax above.

---

## Adding a new content block

The four common add-a-block operations, in one place:

| To add...                                | Which file                 | Which block template                       |
|------------------------------------------|----------------------------|--------------------------------------------|
| A new job / role                         | `content/experience.txt`   | `title / org / dates / bullets / [sub_bullets]` |
| A new publication                        | `content/publications.txt` | `type / title / citation / [primary_badge / muted_badge]` |
| A new degree                             | `content/education.txt`    | `degree / dates / institution`             |
| A new talk / judging entry               | `talks/details.txt`        | `type / title / venue / date / description / media / slides / video / event` |

Every block is separated by a line containing exactly `---`. Order in the file = order on the page (top of file = topmost card).

Bulleted lists (`awards:`, `certificates:`, `highlights:`, `interests:`, `bullets:`, `sub_bullets:`, `tags:`, `items:`) all use the same format: the field name ending in `:` on its own line, followed by indented lines each starting with `- `. A blank line ends the list.

---

## Media — talk images and videos (Cloudinary-hosted)

Talk media is hosted on **Cloudinary**, not GitHub. You upload original full-resolution files; Cloudinary stores them and serves auto-optimized variants (`f_auto,q_auto`) — same visual quality, ~40× smaller download than the raw file. Nothing large ever touches the git repo.

### One-time setup

**1. Install the Cloudinary Python SDK** (only needed for `--upload`; the plain build doesn't require it):

```bash
pip install cloudinary
```

**2. Hardcode your cloud name** near the top of `sync.py`:

```python
CLOUDINARY_CLOUD_NAME = "wbtgpw3v"    # public — safe to commit
```

The cloud name is public (it appears in every image URL). Safe to commit.

**3. Create the credentials file.** Copy `.cloudinary.example` → `.cloudinary` and fill in the API key + secret from https://console.cloudinary.com/ → Dashboard → API Keys:

```bash
cp .cloudinary.example .cloudinary
# then edit .cloudinary and paste the real key + secret
```

`.cloudinary` is gitignored — **it will never be committed**. Alternatively, set them as env vars: `export CLOUDINARY_API_KEY=…` and `export CLOUDINARY_API_SECRET=…`.

### What to install + what to keep on disk

Quick reference — what has to exist on your machine for each operation:

| Operation                                 | Requires                                                                                          |
|-------------------------------------------|---------------------------------------------------------------------------------------------------|
| `python3 sync.py`   (regular build)       | Python 3.9+ only. No SDK, no credentials, no network. Uses `talks/images+videos/manifest.json` if present; falls back to local paths otherwise. |
| `python3 sync.py --check`                 | Same as above.                                                                                    |
| `python3 sync.py --upload`                | Python 3.9+ · `pip install cloudinary` · a `.cloudinary` file (or env vars) with API key + secret · macOS `sips` (built-in, only used to auto-compress images >10 MB) · at least one media file in `talks/images+videos/` |
| `python3 -m http.server 8000` (preview)   | Python 3.9+. If Cloudinary URLs are in the HTML, they load from the internet — you need connectivity. |

**Files that MUST be in the repo (committed to git):**

| Path                                       | What it does                                                                    |
|--------------------------------------------|----------------------------------------------------------------------------------|
| `sync.py`                                  | Build script. Contains the hardcoded `CLOUDINARY_CLOUD_NAME`.                    |
| `.cloudinary.example`                      | Template showing the format of the private credentials file.                     |
| `.gitignore`                               | Enforces the "commit-vs-ignore" rules below.                                     |
| `talks/images+videos/manifest.json`        | Created by `sync.py --upload`. Maps `filename → public_id`. Small JSON file. Needed for the site to serve Cloudinary URLs. |
| `talks/images+videos/README.md`            | Docs for the folder — no content dependency.                                     |
| All `content/*.txt`, `talks/details.txt`, `styles.css`, `index.html`, etc. | Standard site sources / generated pages. |

**Files that MUST exist locally but MUST NOT be committed** (`.gitignore` blocks them):

| Path                                       | What it does                                                                    |
|--------------------------------------------|----------------------------------------------------------------------------------|
| `.cloudinary`                              | Your API key + secret. Read by `sync.py --upload`. Never commit — a leaked secret gives full account access.  Alternative: use env vars, no file. |
| `talks/images+videos/*.JPG`, `*.jpg`, `*.png`, `*.mp4`, ... | Original media files. Present locally as the upload source. Not needed after upload — Cloudinary + manifest cover it — but keep them as a backup source in case you ever want to re-upload at different settings. |

**Which local files are optional to keep after a successful upload:**

- The originals in `talks/images+videos/*.JPG` etc. can be **deleted from disk** if you're tight on space. The site keeps working because:
  - The manifest (committed) remembers each `filename → public_id` mapping
  - Cloudinary has the actual bytes
  - `sync.py` (no `--upload`) generates the same URLs whether the local file exists or not
- Only downsides to deleting locals:
  - You'd need to re-download them (from your camera / Photos library / Cloudinary console) if you ever want to `--upload` again with different settings
  - No local backup if your Cloudinary account is ever suspended or deleted
- Recommended: **keep the originals on disk** (they're gitignored anyway, so they cost you nothing in the repo).

**What happens if someone else clones this repo** (or you clone it on a new machine):

- They get the `manifest.json` — the site builds and serves images from your Cloudinary account immediately, no upload needed
- They do NOT get `.cloudinary` — so they can't `--upload` (which is correct — only you should be pushing to your Cloudinary account)
- They do NOT get the original media files — but they don't need them; the site works from Cloudinary

### Adding new media

1. **Drop the files** — originals, no need to resize/compress — into `talks/images+videos/`:
   ```
   talks/images+videos/DSC00946.JPG
   talks/images+videos/talk-nasiko-clip.mp4
   ```

2. **Upload + rebuild in one shot:**
   ```bash
   python3 sync.py --upload
   ```
   Output:
   ```
   ↑ Uploading DSC00946.JPG  →  talks/DSC00946  (image) ...
       (auto-compressing: 20.1 MB → max 3200 px, quality 85)
       → compressed to 3.4 MB
   ↑ Uploading talk-nasiko-clip.mp4  →  talks/talk-nasiko-clip  (video) ...
   Uploaded 2 file(s). Manifest written to talks/images+videos/manifest.json.
   Regenerating pages with updated Cloudinary URLs...
   Rewrote 1 page(s):
     talks/index.html
   ```

   **Auto-compression:** Cloudinary's free tier caps images at 10 MB per file.
   `sync.py` automatically downsizes larger images (via macOS `sips`, max 3200 px
   longest edge, quality 85) before upload. Your local originals are never
   modified — the compression happens in a temp file that's deleted after the
   upload. Since Cloudinary re-optimizes on delivery anyway (`f_auto,q_auto`),
   the visitor-facing quality is unaffected. Adjust the thresholds via the
   `CLOUDINARY_DOWNSIZE_*` constants near the top of `sync.py`.

   **Videos:** Free tier allows up to 100 MB per video file. No auto-compression
   is applied to videos — if a clip exceeds that, Cloudinary rejects it and
   sync.py surfaces the error verbatim.

3. **Reference the files by filename** in `talks/details.txt` — same as before:
   ```
   media: DSC00946.JPG, talk-nasiko-clip.mp4
   ```
   The extension controls whether `sync.py` emits `<img>` or `<video>`.

4. **Commit the manifest + code** (not the media):
   ```bash
   git add talks/images+videos/manifest.json talks/details.txt talks/index.html
   git commit -m "Add talk media"
   git push
   ```

### How the URLs are generated

`sync.py` reads `talks/images+videos/manifest.json` on every build. For each filename in `details.txt`'s `media:` field:

- **If in the manifest** → generates a Cloudinary delivery URL:
  ```
  https://res.cloudinary.com/<cloud>/image/upload/f_auto,q_auto/talks/DSC00946
  ```
- **If NOT in the manifest** → falls back to a local path (`/talks/images+videos/<filename>`) so `python3 -m http.server 8000` still works for dev preview.

Just running `python3 sync.py` (no `--upload`) is always safe — it never mutates Cloudinary, just re-reads the manifest.

### Recommended file specs

Because Cloudinary transforms images on the fly, you can upload anything and it'll be served optimally. Practical guidelines:

**Images:**
- Aspect ratio: any — but 16:9 gives the best crop for the card layout (`object-fit: cover`)
- Resolution: up to whatever your camera produces — Cloudinary caps served size to the display device
- Format: `.jpg`, `.png`, `.webp`, `.gif` (all accepted)

**Videos:**
- Aspect ratio: 16:9 for consistency with image slides
- Duration: keep short (~30 s) for a personal-site clip
- Format: `.mp4` (H.264 + AAC) recommended; Cloudinary also accepts `.webm`, `.mov`
- Size: **up to Cloudinary's per-file limit** — Free tier: 100 MB per file, 10 MB per HTTP request (larger files use chunked upload, handled by the SDK automatically)

### Bandwidth and storage

Free tier gives 25 credits/mo (~25 GB storage + 25 GB delivered bandwidth combined). For a personal site this is a lot — you'd need thousands of daily visitors to approach the cap.

### Costs & limits

Check current free-tier limits at https://cloudinary.com/pricing. If you approach them, delivery URLs still work; Cloudinary just contacts you before throttling.

### If Cloudinary is unavailable

The site keeps working — every URL in the generated HTML is fetched independently by the browser. If Cloudinary has an outage, images will fail to load but the site's HTML/CSS/text is unaffected. To fully self-host as a fallback, remove `CLOUDINARY_CLOUD_NAME` (set to `""`), commit local media files, and re-run `sync.py` — URLs revert to local paths.

---

## Local preview

Because pages use absolute paths (`/styles.css`, `/about/`), opening `index.html` directly with `file://` will break styles. Use a local server:

```bash
cd suranjangoswami.com
python3 -m http.server 8000
# open http://localhost:8000 — hard-refresh (Cmd+Shift+R) after each sync.py
```

---

## Deploy to GitHub Pages

### 1. Push to a GitHub repo

GitHub username: **`Suranjan-G`**. Fastest path is a **user site**:

```bash
cd suranjangoswami.com
git init
git branch -M main
git add .
git commit -m "Initial site"
gh repo create Suranjan-G.github.io --public --source=. --push
```

A repo named exactly `Suranjan-G.github.io` auto-publishes at `https://suranjan-g.github.io/` (GitHub lowercases the subdomain).

Alternatively — any repo name works if you enable Pages manually:

```bash
gh repo create suranjangoswami-com --public --source=. --push
# then: Settings → Pages → Source: main / (root)
```

### 2. Configure the custom domain

- In the repo: **Settings → Pages → Custom domain → `suranjangoswami.com`** → Save
- Enable **Enforce HTTPS** once the cert provisions (~15 min)
- The `CNAME` file in the repo already has `suranjangoswami.com` — do not delete it

### 3. Add DNS records at Namecheap

Dashboard → Domain List → Manage `suranjangoswami.com` → **Advanced DNS**.

Add these **without touching your existing MX / TXT (email) records**:

| Type  | Host | Value                        | TTL       |
|-------|------|------------------------------|-----------|
| A     | @    | 185.199.108.153              | Automatic |
| A     | @    | 185.199.109.153              | Automatic |
| A     | @    | 185.199.110.153              | Automatic |
| A     | @    | 185.199.111.153              | Automatic |
| CNAME | www  | `Suranjan-G.github.io.`      | Automatic |

DNS propagation: typically 10–60 minutes.

### 4. Verify

- `https://suranjangoswami.com/` → Home
- `https://suranjangoswami.com/about/` → About
- Send a test to `applications@suranjangoswami.com` — email should still work (untouched by the above).

### 5. Ongoing edits (after deploy)

```bash
# edit content/foo.txt or talks/details.txt
python3 sync.py
git add .
git commit -m "Describe what changed"
git push
```

GitHub Pages auto-rebuilds within ~30–60 seconds of every push.

---

## Alternative: host on `<username>.github.io` without a custom domain

If you don't own (or don't want to buy) a personal domain, you can publish the site directly to the free URL GitHub gives every account:

```
https://<your-github-username>.github.io/
```

That URL is yours forever, at no cost, with a valid HTTPS certificate automatically. Everything else in this project — `sync.py`, content editing, Cloudinary hosting, HTML output — works identically. The only differences are (1) skip the `CNAME` file, and (2) skip the DNS section entirely.

### Differences from the custom-domain flow

| | Custom domain (`suranjangoswami.com`)                        | GitHub URL (`<username>.github.io`)                     |
|-|--------------------------------------------------------------|---------------------------------------------------------|
| Repo name | Must be exactly `<username>.github.io` for user-site auto-publish | Same: `<username>.github.io`                       |
| `CNAME` file | **Required** in repo root                                 | **Must NOT be in the repo** (or must be empty)        |
| DNS setup | 4 A records + 1 CNAME at your registrar                     | None. Zero DNS configuration.                          |
| HTTPS | Manually enable "Enforce HTTPS" after DNS propagates            | Automatic — HTTPS works out of the box, no toggle       |
| Wait time to go live | 10–60 min for DNS propagation + cert                 | ~60 seconds after push                                 |
| Cost | Domain registration (~$10-20/year) + email hosting if you want it | $0 forever                                             |

### Steps

1. **Delete the `CNAME` file** before your first push (it exists in this project because the primary deployment uses a custom domain):
   ```bash
   rm CNAME
   ```

2. **Adjust `.gitignore`** — the `CNAME` line isn't in `.gitignore`, so `rm` + commit is enough. If you'd rather preserve the file for future use, comment it out:
   ```
   # (empty CNAME file — restore your custom domain here if you ever buy one)
   ```
   An empty `CNAME` is treated the same as no `CNAME` — GitHub won't try to redirect.

3. **Create the repo and push** (substitute your actual GitHub username):
   ```bash
   cd path/to/suranjangoswami.com
   git init
   git branch -M main
   git config --local user.name "Your Name"
   git config --local user.email "you@example.com"
   git add .
   git commit -m "Initial site"
   gh repo create <your-username>.github.io --public --source=. --push
   ```

4. **Wait ~60 seconds**, then open:
   ```
   https://<your-username>.github.io/
   ```
   (GitHub lowercases the subdomain, so a username of `Jane-Doe` becomes `jane-doe.github.io`. Your profile URL keeps the original case.)

5. **Verify build status** (optional):
   ```bash
   gh api "repos/<your-username>/<your-username>.github.io/pages" \
     --jq '{status, custom_domain: .cname, https_enforced}'
   ```
   Expected: `status: built`, `custom_domain: null`, `https_enforced: true` (GitHub enforces HTTPS by default on `.github.io` URLs).

### One-time content changes

Because absolute paths in the HTML (`/styles.css`, `/about/`, `/talks/`) are served at the domain root, everything Just Works on `<username>.github.io/` — no path prefix rewriting needed. This is why user-site repos (named exactly `<username>.github.io`) are simpler than project-site repos (any other name), which would need `/<repo-name>/` prefixes everywhere.

### If you buy a custom domain later

You can switch from the free `.github.io` URL to a custom domain any time without breaking the existing URL — both will work in parallel until you set the primary one in Pages settings.

1. Recreate the `CNAME` file with your new domain:
   ```bash
   echo "yourdomain.com" > CNAME
   ```
2. Follow the [Deploy to GitHub Pages](#deploy-to-github-pages) section from Step 3 (DNS records) onward.
3. Your `<username>.github.io/` URL will start 301-redirecting to `https://yourdomain.com/` once the custom domain is configured.

### Sharing the URL

Some places you'd share the URL — GitHub profile, LinkedIn, CV, email signature, business cards. The `<username>.github.io` form works everywhere; you don't need to buy a domain just to have a shareable link.

---

## Extending the pipeline (new page / new section)

To add a whole new section (e.g. a `/blog/`, `/press/`, `/photos/`):

1. **Create the source file.** e.g. `content/blog.txt` with `---`-separated blocks.
2. **In `sync.py`:**
   - Add a line in `load_all()` to parse it: `blog = parse_blocks(CONTENT / "blog.txt")`.
   - Write a `build_blog(profile, blog)` function that returns the full HTML string (use `page_shell(...)` as a wrapper — copy `build_publications` or `build_talks` as a starting template).
   - Add an entry in `build_all()`: `"blog/index.html": build_blog(data["profile"], data["blog"])`.
3. **Add the nav item.** In `sync.py`, add `("Blog", "/blog/")` to the `NAV_ITEMS` list.
4. **Run `python3 sync.py`.** The new page is created and the nav updates automatically on every existing page.

The parser (`parse_blocks`), inline formatter (`md_inline`), page wrapper (`page_shell`), and the shared nav/footer builders are all reusable — a new section usually needs only its own `build_*` function.
