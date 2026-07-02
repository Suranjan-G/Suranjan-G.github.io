#!/usr/bin/env python3
"""
sync.py — Rebuild every page of suranjangoswami.com from content/*.txt.

Usage
-----
    python3 sync.py            # rebuild all pages from content/*.txt
    python3 sync.py --check    # exit 1 if any HTML would change (for CI)
    python3 sync.py --upload   # push any new/changed files in
                               # talks/images+videos/ to Cloudinary, then rebuild
                               # (requires: pip install cloudinary  +  credentials
                               #  in a `.cloudinary` file at repo root OR env vars)

Reads
-----
    content/profile.txt       — name, tagline, hero, bio, contact, highlights, interests
    content/experience.txt    — work history (each block = one job)
    content/publications.txt  — highlighted + regular papers + datasets
    content/education.txt     — degrees
    content/awards.txt        — awards, certificates, hobbies
    content/skills.txt        — grouped skill tags (Domains / Tools / Hardware)
    content/projects.txt      — one-block file: bulleted list of selected projects
    talks/details.txt         — talks and judging entries (colocated with the
                                talks/images+videos/ folder for editing ergonomics)
    talks/images+videos/manifest.json
                              — filename → Cloudinary public_id map (committed;
                                written by `sync.py --upload`; read on every build)

Writes
------
    index.html, about/index.html, experience/index.html,
    publications/index.html, talks/index.html

Third-party deps
----------------
    None for `sync.py` / `sync.py --check`.
    `sync.py --upload` requires the `cloudinary` package: `pip install cloudinary`.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"

# ============================================================
# Cloudinary configuration
# ============================================================
#
# Cloud name is PUBLIC — appears in every asset URL the browser fetches.
# Safe to hardcode + commit. Set it here, or leave "" and export
# CLOUDINARY_CLOUD_NAME=<name> in your shell.
CLOUDINARY_CLOUD_NAME = "wbtgpw3v"

# API key + secret are PRIVATE. Do NOT put them here or anywhere in the repo.
# Store them in a `.cloudinary` file at repo root (this file is gitignored):
#     CLOUDINARY_API_KEY=1234567890
#     CLOUDINARY_API_SECRET=abcdefghijklmnop
# Or export them as CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET env vars.
CREDENTIALS_FILE = ROOT / ".cloudinary"

# Delivery transformations applied to every image / video URL sync.py emits.
#   f_auto = pick the best format per browser (WebP / AVIF / JPEG fallback)
#   q_auto = pick optimal quality per content (preserves detail)
# Same visual quality as the uploaded original; typically 30-80x smaller download.
CLOUDINARY_IMG_TRANSFORM = "f_auto,q_auto"
CLOUDINARY_VIDEO_TRANSFORM = "q_auto,f_auto"

# Open Graph / Twitter card preview image. Same image used on every page
# (LinkedIn, Twitter, Slack, etc. show this when the URL is shared).
# Sized to 1200×630 (Facebook/LinkedIn recommended, ~1.91:1) via Cloudinary
# transformations — no separate image file needed.
#   c_fill  = crop to exact size
#   g_auto  = smart gravity (Cloudinary picks the best crop focus)
#   f_auto,q_auto = auto format + quality
CLOUDINARY_OG_IMAGE_PUBLIC_ID = "talks/DSC00948"
CLOUDINARY_OG_IMAGE_TRANSFORM = "w_1200,h_630,c_fill,g_auto,f_auto,q_auto"

# Where sync.py stores the filename → public_id map. Committed to git so anyone
# with the repo can build the site without re-uploading anything.
CLOUDINARY_MANIFEST = ROOT / "talks" / "images+videos" / "manifest.json"

# Local fallback: used when a file is present in details.txt but missing from
# the manifest (i.e. not yet uploaded). Also used when CLOUDINARY_CLOUD_NAME
# is empty. Lets the site work in offline / dev mode.
MEDIA_URL_PREFIX = "/talks/images+videos"

# Cloudinary free tier caps images at 10 MB per file. Files larger than this
# get auto-downscaled with macOS `sips` before upload. Visual quality on the
# rendered site is unaffected — Cloudinary re-optimizes on delivery anyway.
# Local originals in talks/images+videos/ are never modified.
CLOUDINARY_MAX_UPLOAD_BYTES = 10 * 1024 * 1024        # 10 MB
CLOUDINARY_DOWNSIZE_MAX_DIM = 3200                    # longest edge, px
CLOUDINARY_DOWNSIZE_QUALITY = 85                      # JPEG quality, 0-100


def cloud_name() -> str:
    return CLOUDINARY_CLOUD_NAME or os.environ.get("CLOUDINARY_CLOUD_NAME", "") or ""


def load_manifest() -> dict:
    if CLOUDINARY_MANIFEST.exists():
        try:
            return json.loads(CLOUDINARY_MANIFEST.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"warning: {CLOUDINARY_MANIFEST} is not valid JSON — ignoring.",
                  file=sys.stderr)
    return {}


def cloudinary_url(public_id: str, kind: str) -> str:
    """
    Build a Cloudinary delivery URL.
      kind = "image" | "video"
    Returns "" if cloud name is not configured.
    """
    cn = cloud_name()
    if not cn:
        return ""
    tx = CLOUDINARY_IMG_TRANSFORM if kind == "image" else CLOUDINARY_VIDEO_TRANSFORM
    return f"https://res.cloudinary.com/{cn}/{kind}/upload/{tx}/{public_id}"


def og_image_url() -> str:
    """
    URL for the Open Graph / Twitter preview image. Fixed dimensions 1200×630
    via Cloudinary transforms — same image shared across every page's <head>.
    Returns "" if cloud name is not configured.
    """
    cn = cloud_name()
    if not cn:
        return ""
    return (
        f"https://res.cloudinary.com/{cn}/image/upload/"
        f"{CLOUDINARY_OG_IMAGE_TRANSFORM}/{CLOUDINARY_OG_IMAGE_PUBLIC_ID}"
    )


def media_src(filename: str, kind: str, manifest: dict) -> str:
    """
    Resolve a media reference from details.txt into a delivery URL.
      1. If the filename is in the manifest AND cloud name is configured →
         Cloudinary URL (auto-optimized).
      2. Otherwise → local /talks/images+videos/ path (dev fallback).
    """
    entry = manifest.get(filename)
    if entry and cloud_name():
        return cloudinary_url(entry["public_id"], entry.get("kind", kind))
    return f"{MEDIA_URL_PREFIX}/{filename}"


# ============================================================
# Parser — a very small subset of YAML-like syntax
# ============================================================

def parse_blocks(path: Path) -> list[dict]:
    """
    Parse a content file. Returns list of dicts, one per `---` block.
    Supports:
      - `# comment` lines
      - `field: value` (single-line string field)
      - `field:` followed by indented `- item` lines (list field)
      - `---` on its own line as block separator
    A blank line ends any open list.
    """
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    blocks: list[dict] = []
    current: dict = {}
    active_list_key: str | None = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            active_list_key = None
            continue
        if stripped.startswith("#"):
            continue

        if stripped == "---":
            if current:
                blocks.append(current)
            current = {}
            active_list_key = None
            continue

        indent = len(line) - len(line.lstrip())

        # List item under an open list field
        if stripped.startswith("- ") and active_list_key is not None and indent > 0:
            current[active_list_key].append(stripped[2:].strip())
            continue

        # Field: value  OR  Field:  (opens a list)
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if m and indent == 0:
            key, value = m.group(1), m.group(2).strip()
            if value:
                current[key] = value
                active_list_key = None
            else:
                current[key] = []
                active_list_key = key
            continue

    if current:
        blocks.append(current)
    return blocks


def parse_single(path: Path) -> dict:
    """For files with a single entry (profile.txt). Returns first block or {}."""
    blocks = parse_blocks(path)
    return blocks[0] if blocks else {}


# ============================================================
# HTML helpers
# ============================================================

def esc(value) -> str:
    """HTML-escape; None → ''."""
    return html.escape(str(value or ""), quote=True)


def md_inline(text) -> str:
    """
    Very small inline-markdown → HTML pass:
      **bold**       → <strong>...</strong>
      _italic_       → <em>...</em>
      ==highlight==  → <span class="highlight">...</span>
      [text](url)    → <a href="url">text</a>
    Everything else is HTML-escaped. Safe by default.
    """
    if text is None:
        return ""
    text = html.escape(str(text), quote=True)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"==(.+?)==", r'<span class="highlight">\1</span>', text)
    text = re.sub(r"(?<![A-Za-z0-9_])_([^_]+)_(?![A-Za-z0-9_])", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{esc(m.group(2))}">{esc(m.group(1))}</a>',
        text,
    )
    return text


def get_ext(fname: str) -> str:
    return fname.rsplit(".", 1)[-1].lower() if "." in fname else ""


IMAGE_EXTS = {"jpg", "jpeg", "png", "webp", "gif", "heic", "heif", "avif", "tiff", "tif", "bmp"}
VIDEO_EXTS = {"mp4", "webm", "mov", "m4v"}


# ============================================================
# Shared shell (nav, footer, page wrapper)
# ============================================================

NAV_ITEMS = [
    ("Home", "/"),
    ("About", "/about/"),
    ("Experience", "/experience/"),
    ("Publications", "/publications/"),
    ("Talks / Judging", "/talks/"),
]


def nav_html(active_href: str) -> str:
    lis = []
    for label, href in NAV_ITEMS:
        cls = ' class="active"' if href == active_href else ""
        lis.append(f'        <li><a href="{href}"{cls}>{label}</a></li>')
    return "\n".join(lis)


def footer_html(profile: dict) -> str:
    return (
        '  <footer>\n'
        '    <div>\n'
        f'      © {esc(profile.get("name", ""))} ·\n'
        f'      <a href="mailto:{esc(profile.get("email", ""))}">Email</a> ·\n'
        f'      <a href="{esc(profile.get("linkedin", ""))}">LinkedIn</a> ·\n'
        f'      <a href="{esc(profile.get("scholar", ""))}">Scholar</a> ·\n'
        f'      <a href="{esc(profile.get("dataport", ""))}">IEEE Dataport</a>\n'
        '    </div>\n'
        '  </footer>\n'
    )


AUTOGEN_WARNING = (
    "<!-- ================================================================\n"
    "     AUTO-GENERATED by sync.py from content/*.txt.\n"
    "     Do NOT edit this HTML by hand — your changes will be overwritten\n"
    "     the next time you run `python3 sync.py`.\n"
    "     To change site content, edit the matching file in content/,\n"
    "     then re-run sync.py.\n"
    "     ================================================================ -->"
)


def page_shell(title, description, canonical, active_href, main_html, profile,
               wide=False, extra_body=""):
    body_class = ' class="talks"' if wide else ""  # noqa (currently unused)
    og_img = og_image_url()
    og_block = ""
    if og_img:
        og_alt = f"{profile.get('name', '')} — {profile.get('tagline', '')}".strip(" —")
        og_block = (
            '  <meta property="og:type" content="website">\n'
            f'  <meta property="og:url" content="{canonical}">\n'
            f'  <meta property="og:title" content="{esc(title)}">\n'
            f'  <meta property="og:description" content="{esc(description)}">\n'
            f'  <meta property="og:image" content="{og_img}">\n'
            '  <meta property="og:image:width" content="1200">\n'
            '  <meta property="og:image:height" content="630">\n'
            f'  <meta property="og:image:alt" content="{esc(og_alt)}">\n'
            '  <meta name="twitter:card" content="summary_large_image">\n'
            f'  <meta name="twitter:title" content="{esc(title)}">\n'
            f'  <meta name="twitter:description" content="{esc(description)}">\n'
            f'  <meta name="twitter:image" content="{og_img}">\n'
        )
    return (
        '<!doctype html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'  <title>{esc(title)}</title>\n'
        f'  <meta name="description" content="{esc(description)}">\n'
        '  <link rel="stylesheet" href="/styles.css">\n'
        f'  <link rel="canonical" href="{canonical}">\n'
        f'{og_block}'
        '</head>\n'
        '<body>\n'
        f'{AUTOGEN_WARNING}\n'
        '  <nav>\n'
        '    <div class="inner">\n'
        f'      <a href="/" class="brand">{esc(profile.get("name", ""))}</a>\n'
        '      <ul>\n'
        f'{nav_html(active_href)}\n'
        '      </ul>\n'
        '    </div>\n'
        '  </nav>\n\n'
        f'{main_html}\n'
        f'{footer_html(profile)}'
        f'{extra_body}'
        '</body>\n'
        '</html>\n'
    )


# ============================================================
# Page builder: Home
# ============================================================

def build_home(profile: dict) -> str:
    highlights = profile.get("highlights", [])
    highlights_html = "\n".join(
        f'        <li>{md_inline(h)}</li>' for h in highlights
    )
    interests = profile.get("interests", [])
    interests_html = "\n".join(
        f'        <span class="skill-tag">{esc(t)}</span>' for t in interests
    )

    main = (
        '  <main>\n'
        '    <section class="hero">\n'
        f'      <h1>{esc(profile.get("name", ""))}</h1>\n'
        f'      <p class="tagline">{esc(profile.get("tagline", ""))}</p>\n'
        f'      <p>{md_inline(profile.get("hero_intro", ""))}</p>\n'
        f'      <p>{md_inline(profile.get("hero_recent", ""))}</p>\n'
        '      <div class="contact-links">\n'
        f'        <a href="mailto:{esc(profile.get("email", ""))}">{esc(profile.get("email", ""))}</a>\n'
        f'        <a href="{esc(profile.get("linkedin", ""))}">LinkedIn</a>\n'
        f'        <a href="{esc(profile.get("scholar", ""))}">Google Scholar</a>\n'
        f'        <a href="{esc(profile.get("dataport", ""))}">IEEE Dataport</a>\n'
        '      </div>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Selected highlights</h2>\n'
        '      <ul>\n'
        f'{highlights_html}\n'
        '      </ul>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Research interests</h2>\n'
        '      <div class="skill-tags">\n'
        f'{interests_html}\n'
        '      </div>\n'
        '    </section>\n'
        '  </main>\n'
    )
    return page_shell(
        title=profile.get("home_title", "Suranjan Goswami"),
        description=profile.get("home_description", ""),
        canonical="https://suranjangoswami.com/",
        active_href="/",
        main_html=main,
        profile=profile,
    )


# ============================================================
# Page builder: About
# ============================================================

def build_about(profile: dict, education: list[dict], awards: dict) -> str:
    summary = md_inline(profile.get("about_summary", ""))
    trajectory = profile.get("about_trajectory", [])
    trajectory_html = "\n".join(f'      <p>{md_inline(p)}</p>' for p in trajectory)

    edu_html_parts = []
    for e in education:
        edu_html_parts.append(
            '      <div class="job">\n'
            '        <div class="job-header">\n'
            f'          <span class="job-title">{esc(e.get("degree", ""))}</span>\n'
            f'          <span class="job-dates">{esc(e.get("dates", ""))}</span>\n'
            '        </div>\n'
            f'        <div class="job-org">{md_inline(e.get("institution", ""))}</div>\n'
            '      </div>'
        )
    edu_html = "\n".join(edu_html_parts)

    def bullets(items, badges=False):
        rendered = []
        for it in items:
            if badges and it.startswith("!"):
                # e.g. "!A* Publication at ICLR 2026" → <span class="badge">A*</span>
                m = re.match(r"^!([^ ]+)\s+(.*)$", it)
                if m:
                    rendered.append(
                        f'        <li><span class="badge">{esc(m.group(1))}</span> {md_inline(m.group(2))}</li>'
                    )
                    continue
            rendered.append(f'        <li>{md_inline(it)}</li>')
        return "\n".join(rendered)

    awards_html = bullets(awards.get("awards", []), badges=True)
    certs_html = bullets(awards.get("certificates", []))
    hobbies = md_inline(awards.get("hobbies", ""))

    main = (
        '  <main>\n'
        '    <h1>About</h1>\n'
        f'    <p class="section-lead">{md_inline(profile.get("about_lead", ""))}</p>\n\n'
        '    <section>\n'
        '      <h2>Summary</h2>\n'
        f'      <p>{summary}</p>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Trajectory</h2>\n'
        f'{trajectory_html}\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Education</h2>\n'
        f'{edu_html}\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Awards &amp; recognition</h2>\n'
        '      <ul>\n'
        f'{awards_html}\n'
        '      </ul>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Certificates &amp; training</h2>\n'
        '      <ul>\n'
        f'{certs_html}\n'
        '      </ul>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Beyond research</h2>\n'
        f'      <p>{hobbies}</p>\n'
        '    </section>\n'
        '  </main>\n'
    )
    return page_shell(
        title=f"About — {profile.get('name', '')}",
        description=profile.get("about_description", ""),
        canonical="https://suranjangoswami.com/about/",
        active_href="/about/",
        main_html=main,
        profile=profile,
    )


# ============================================================
# Page builder: Experience
# ============================================================

def build_experience(profile: dict, jobs: list[dict], skills: list[dict], projects: list[str]) -> str:
    def render_job(j):
        bullets = j.get("bullets", [])
        sub_bullets = j.get("sub_bullets", [])
        bullet_html = []
        for i, b in enumerate(bullets):
            is_last = i == len(bullets) - 1
            if is_last and sub_bullets:
                inner = "\n".join(f'              <li>{md_inline(s)}</li>' for s in sub_bullets)
                bullet_html.append(
                    f'          <li>{md_inline(b)}\n'
                    '            <ul>\n'
                    f'{inner}\n'
                    '            </ul>\n'
                    '          </li>'
                )
            else:
                bullet_html.append(f'          <li>{md_inline(b)}</li>')
        bullets_rendered = "\n".join(bullet_html)
        return (
            '      <div class="job">\n'
            '        <div class="job-header">\n'
            f'          <span class="job-title">{esc(j.get("title", ""))}</span>\n'
            f'          <span class="job-dates">{esc(j.get("dates", ""))}</span>\n'
            '        </div>\n'
            f'        <div class="job-org">{esc(j.get("org", ""))}</div>\n'
            '        <ul>\n'
            f'{bullets_rendered}\n'
            '        </ul>\n'
            '      </div>'
        )

    jobs_html = "\n\n".join(render_job(j) for j in jobs)

    proj_html = "\n".join(f'        <li>{md_inline(p)}</li>' for p in projects)

    skill_sections = []
    for group in skills:
        heading = group.get("heading", "")
        tags = group.get("tags", [])
        tags_html = "\n".join(
            f'        <span class="skill-tag">{esc(t)}</span>' for t in tags
        )
        skill_sections.append(
            f'      <h3>{esc(heading)}</h3>\n'
            '      <div class="skill-tags">\n'
            f'{tags_html}\n'
            '      </div>'
        )
    skills_html = "\n".join(skill_sections)

    main = (
        '  <main>\n'
        '    <h1>Experience</h1>\n'
        f'    <p class="section-lead">{md_inline(profile.get("experience_lead", ""))}</p>\n\n'
        '    <section>\n'
        '      <h2>Work history</h2>\n\n'
        f'{jobs_html}\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Selected projects</h2>\n'
        '      <ul>\n'
        f'{proj_html}\n'
        '      </ul>\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Skills</h2>\n'
        f'{skills_html}\n'
        '    </section>\n'
        '  </main>\n'
    )
    return page_shell(
        title=f"Experience — {profile.get('name', '')}",
        description=profile.get("experience_description", ""),
        canonical="https://suranjangoswami.com/experience/",
        active_href="/experience/",
        main_html=main,
        profile=profile,
    )


# ============================================================
# Page builder: Publications
# ============================================================

def build_publications(profile: dict, pubs: list[dict]) -> str:
    highlights = [p for p in pubs if p.get("type") == "highlight"]
    papers = [p for p in pubs if p.get("type") == "paper"]
    datasets = [p for p in pubs if p.get("type") == "dataset"]

    def render_highlight(p):
        badges = ""
        for b in ("primary_badge", "muted_badge"):
            val = p.get(b)
            if val:
                cls = "badge" if b == "primary_badge" else "badge muted"
                badges += f'<span class="{cls}">{esc(val)}</span> '
        return (
            '      <div class="pub-highlight">\n'
            f'        <div>{badges.strip()}</div>\n'
            f'        <div class="pub-title" style="margin-top: 0.5rem;">{md_inline(p.get("title", ""))}</div>\n'
            f'        <div class="pub-meta">{md_inline(p.get("citation", ""))}</div>\n'
            '      </div>'
        )

    def render_publication(p):
        return (
            '      <div class="publication">\n'
            f'        <div class="pub-title">{md_inline(p.get("title", ""))}</div>\n'
            f'        <div class="pub-meta">{md_inline(p.get("citation", ""))}</div>\n'
            '      </div>'
        )

    hl_html = "\n\n".join(render_highlight(p) for p in highlights)
    papers_html = "\n\n".join(render_publication(p) for p in papers)
    datasets_html = "\n\n".join(render_publication(p) for p in datasets)

    main = (
        '  <main>\n'
        '    <h1>Publications</h1>\n'
        f'    <p class="section-lead">{md_inline(profile.get("publications_lead", ""))}</p>\n\n'
        '    <section>\n'
        '      <h2>Highlighted</h2>\n\n'
        f'{hl_html}\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Journal &amp; conference papers</h2>\n\n'
        f'{papers_html}\n'
        '    </section>\n\n'
        '    <section>\n'
        '      <h2>Open datasets</h2>\n\n'
        f'{datasets_html}\n'
        '    </section>\n'
        '  </main>\n'
    )
    return page_shell(
        title=f"Publications — {profile.get('name', '')}",
        description=profile.get("publications_description", ""),
        canonical="https://suranjangoswami.com/publications/",
        active_href="/publications/",
        main_html=main,
        profile=profile,
    )


# ============================================================
# Page builder: Talks / Judging
# ============================================================

TALKS_GALLERY_SCRIPT = """  <script>
    document.querySelectorAll('.talk-gallery').forEach(function (gallery) {
      var track = gallery.querySelector('.talk-gallery-track');
      if (!track) return;
      var slides = track.querySelectorAll('img, video');
      var count = slides.length;

      if (count <= 1) {
        gallery.classList.add('single-image');
        return;
      }

      var countBadge = gallery.querySelector('.talk-gallery-count');
      var dotsContainer = gallery.querySelector('.talk-gallery-dots');
      var prevBtn = gallery.querySelector('.talk-gallery-prev');
      var nextBtn = gallery.querySelector('.talk-gallery-next');

      var dots = [];
      if (dotsContainer) {
        for (var i = 0; i < count; i++) {
          var dot = document.createElement('button');
          dot.type = 'button';
          dot.setAttribute('aria-label', 'Go to image ' + (i + 1));
          (function (idx) {
            dot.addEventListener('click', function () {
              track.scrollTo({ left: track.clientWidth * idx, behavior: 'smooth' });
            });
          })(i);
          dotsContainer.appendChild(dot);
          dots.push(dot);
        }
      }

      function currentIndex() {
        return Math.round(track.scrollLeft / track.clientWidth);
      }
      function syncUI() {
        var idx = currentIndex();
        dots.forEach(function (d, i) {
          d.setAttribute('aria-current', i === idx ? 'true' : 'false');
        });
        if (countBadge) countBadge.textContent = (idx + 1) + ' / ' + count;
      }

      var scrollRaf = null;
      track.addEventListener('scroll', function () {
        if (scrollRaf) cancelAnimationFrame(scrollRaf);
        scrollRaf = requestAnimationFrame(syncUI);
      });
      if (prevBtn) prevBtn.addEventListener('click', function () {
        track.scrollBy({ left: -track.clientWidth, behavior: 'smooth' });
      });
      if (nextBtn) nextBtn.addEventListener('click', function () {
        track.scrollBy({ left: track.clientWidth, behavior: 'smooth' });
      });
      syncUI();
    });
  </script>
"""


def build_talks(profile: dict, talks: list[dict], manifest: dict) -> str:
    def render_slide(fname, alt):
        ext = get_ext(fname)
        kind = "video" if ext in VIDEO_EXTS else "image"
        src = media_src(fname, kind, manifest)
        if kind == "video":
            return (f'            <video controls muted playsinline '
                    f'preload="metadata" src="{esc(src)}"></video>')
        return f'            <img src="{esc(src)}" alt="{esc(alt)}">'

    def render_card(t):
        raw_media = t.get("media", "")
        if isinstance(raw_media, list):
            filenames = [x.strip() for x in raw_media if x.strip()]
        else:
            filenames = [x.strip() for x in str(raw_media).split(",") if x.strip()]
        title = t.get("title", "")
        card_type = (t.get("type") or "talk").strip().lower()
        badge_class = "judge" if card_type == "judge" else "talk"
        badge_text = "Judging" if card_type == "judge" else "Talk"
        slides_html = "\n".join(
            render_slide(f, f"{title} — {i + 1}") for i, f in enumerate(filenames)
        )
        venue = esc(t.get("venue", ""))
        date = esc(t.get("date", ""))
        venue_line_parts = [x for x in [venue, date] if x]
        venue_line = " · ".join(venue_line_parts)

        # Optional links
        link_bits = []
        for key, label in [("slides", "Slides"), ("video", "Video"), ("event", "Event page")]:
            url = (t.get(key) or "").strip()
            if url:
                link_bits.append(f'            <a href="{esc(url)}">{label}</a>')
        links_html = ""
        if link_bits:
            links_html = (
                '          <div class="talk-links">\n'
                + "\n".join(link_bits) + '\n'
                '          </div>\n'
            )

        return (
            '      <article class="talk-card">\n'
            '        <div class="talk-gallery">\n'
            '          <div class="talk-gallery-track">\n'
            f'{slides_html}\n'
            '          </div>\n'
            '          <span class="talk-gallery-count"></span>\n'
            '          <button class="talk-gallery-prev" type="button" aria-label="Previous">&#8249;</button>\n'
            '          <button class="talk-gallery-next" type="button" aria-label="Next">&#8250;</button>\n'
            '          <div class="talk-gallery-dots"></div>\n'
            '        </div>\n'
            '        <div class="talk-card-body">\n'
            f'          <span class="type-tag {badge_class}">{badge_text}</span>\n'
            f'          <h3>{md_inline(title)}</h3>\n'
            f'          <div class="venue">{venue_line}</div>\n'
            f'          <p class="desc">{md_inline(t.get("description", ""))}</p>\n'
            f'{links_html}'
            '        </div>\n'
            '      </article>'
        )

    cards_html = "\n\n".join(render_card(t) for t in talks) if talks else \
        '      <!-- No entries in content/talks.txt yet -->'

    main = (
        '  <main class="wide">\n'
        '    <h1>Talks / Judging</h1>\n'
        f'    <p class="section-lead">{md_inline(profile.get("talks_lead", ""))}</p>\n\n'
        '    <div class="talks-grid">\n\n'
        f'{cards_html}\n\n'
        '    </div>\n'
        '  </main>\n'
    )
    return page_shell(
        title=f"Talks / Judging — {profile.get('name', '')}",
        description=profile.get("talks_description", ""),
        canonical="https://suranjangoswami.com/talks/",
        active_href="/talks/",
        main_html=main,
        profile=profile,
        wide=True,
        extra_body=TALKS_GALLERY_SCRIPT,
    )


# ============================================================
# Driver
# ============================================================

PAGES = [
    ("index.html", "build_home"),
    ("about/index.html", "build_about"),
    ("experience/index.html", "build_experience"),
    ("publications/index.html", "build_publications"),
    ("talks/index.html", "build_talks"),
]


def load_all() -> dict:
    profile = parse_single(CONTENT / "profile.txt")
    jobs = parse_blocks(CONTENT / "experience.txt")

    projects_block = parse_single(CONTENT / "projects.txt")
    projects = projects_block.get("items", [])

    publications = parse_blocks(CONTENT / "publications.txt")
    education = parse_blocks(CONTENT / "education.txt")

    awards = parse_single(CONTENT / "awards.txt")

    skills = parse_blocks(CONTENT / "skills.txt")
    talks = parse_blocks(ROOT / "talks" / "details.txt")
    manifest = load_manifest()

    return {
        "profile": profile,
        "jobs": jobs,
        "projects": projects,
        "publications": publications,
        "education": education,
        "awards": awards,
        "skills": skills,
        "talks": talks,
        "manifest": manifest,
    }


def build_all(data: dict) -> dict[str, str]:
    return {
        "index.html": build_home(data["profile"]),
        "about/index.html": build_about(data["profile"], data["education"], data["awards"]),
        "experience/index.html": build_experience(
            data["profile"], data["jobs"], data["skills"], data["projects"]
        ),
        "publications/index.html": build_publications(data["profile"], data["publications"]),
        "talks/index.html": build_talks(data["profile"], data["talks"], data["manifest"]),
    }


# ============================================================
# Cloudinary upload — used only by `sync.py --upload`
# ============================================================

def _load_credential(env_var: str) -> str | None:
    """Look up a credential in env, then in the .cloudinary file at repo root."""
    val = os.environ.get(env_var)
    if val:
        return val.strip()
    if CREDENTIALS_FILE.exists():
        for raw in CREDENTIALS_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == env_var:
                return v.strip().strip('"').strip("'")
    return None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _sips_compress(src: Path, dst: Path, max_dim: int, quality: int) -> None:
    """Downsize + re-encode an image using macOS's built-in `sips`."""
    is_png = get_ext(src.name) == "png"
    fmt = "png" if is_png else "jpeg"
    cmd = ["sips", "-Z", str(max_dim), "-s", "format", fmt]
    if not is_png:
        cmd += ["-s", "formatOptions", str(quality)]
    cmd += [str(src), "--out", str(dst)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"sips failed for {src.name}:\n{result.stderr.strip()}")


def _prepare_for_upload(path: Path) -> tuple[Path, bool]:
    """
    Return (path_to_upload, is_temp).
      - If file is under Cloudinary's per-file limit: return original, is_temp=False.
      - If file is over the limit AND is an image: create a downscaled copy in a
        temp dir, return that, is_temp=True.
      - Videos over the limit are returned as-is (Cloudinary allows 100 MB videos
        on free tier; if a video is over that, the upload will fail with a clear
        message).
    Local original file is never modified.
    """
    size = path.stat().st_size
    if size <= CLOUDINARY_MAX_UPLOAD_BYTES:
        return path, False
    if get_ext(path.name) in VIDEO_EXTS:
        return path, False
    if shutil.which("sips") is None:
        raise RuntimeError(
            f"{path.name} is {size / 1024 / 1024:.1f} MB, over Cloudinary's "
            f"{CLOUDINARY_MAX_UPLOAD_BYTES / 1024 / 1024:.0f} MB free-tier "
            f"limit. macOS `sips` is not available for auto-compression. "
            f"Compress manually to <10 MB and try again."
        )
    tmp_dir = Path(tempfile.mkdtemp(prefix="sync-cloudinary-"))
    ext_out = ".png" if get_ext(path.name) == "png" else ".jpg"
    tmp_path = tmp_dir / (path.stem + ext_out)
    print(f"    (auto-compressing: {size / 1024 / 1024:.1f} MB → "
          f"max {CLOUDINARY_DOWNSIZE_MAX_DIM} px, "
          f"quality {CLOUDINARY_DOWNSIZE_QUALITY})")
    _sips_compress(path, tmp_path, CLOUDINARY_DOWNSIZE_MAX_DIM,
                   CLOUDINARY_DOWNSIZE_QUALITY)
    new_size = tmp_path.stat().st_size
    print(f"    → compressed to {new_size / 1024 / 1024:.1f} MB")
    return tmp_path, True


def _save_manifest(manifest: dict) -> None:
    """Write manifest atomically (write to temp file then rename)."""
    CLOUDINARY_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLOUDINARY_MANIFEST.with_suffix(CLOUDINARY_MANIFEST.suffix + ".tmp")
    tmp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    tmp.replace(CLOUDINARY_MANIFEST)


def upload_command() -> None:
    """
    Scan talks/images+videos/ for local media, upload anything new or changed
    to Cloudinary, and update the manifest. Missing SDK / credentials = clear
    error + exit 1 (nothing else touched).
    """
    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError:
        print("error: Cloudinary SDK not installed.", file=sys.stderr)
        print("       Run:  pip install cloudinary", file=sys.stderr)
        sys.exit(1)

    cn = cloud_name()
    api_key = _load_credential("CLOUDINARY_API_KEY")
    api_secret = _load_credential("CLOUDINARY_API_SECRET")
    missing = [n for n, v in [
        ("CLOUDINARY_CLOUD_NAME (hardcode in sync.py or export as env)", cn),
        ("CLOUDINARY_API_KEY (in .cloudinary file or env)", api_key),
        ("CLOUDINARY_API_SECRET (in .cloudinary file or env)", api_secret),
    ] if not v]
    if missing:
        print("error: missing Cloudinary credentials:", file=sys.stderr)
        for m in missing:
            print(f"  - {m}", file=sys.stderr)
        sys.exit(1)

    cloudinary.config(cloud_name=cn, api_key=api_key,
                      api_secret=api_secret, secure=True)

    manifest = load_manifest()
    media_dir = ROOT / "talks" / "images+videos"
    uploadable = IMAGE_EXTS | VIDEO_EXTS

    files = sorted(
        p for p in media_dir.iterdir()
        if p.is_file()
        and not p.name.startswith(".")
        and get_ext(p.name) in uploadable
    )

    if not files:
        print(f"No uploadable media found in {media_dir}. "
              f"Supported extensions: {sorted(uploadable)}")
        return

    uploaded = 0
    for path in files:
        digest = _sha256(path)
        prior = manifest.get(path.name)
        if prior and prior.get("sha256") == digest:
            print(f"  = {path.name} (unchanged, skipping)")
            continue

        kind = "video" if get_ext(path.name) in VIDEO_EXTS else "image"
        public_id = f"talks/{path.stem}"  # e.g. talks/DSC00946
        print(f"  ↑ Uploading {path.name}  →  {public_id}  ({kind}) ...")

        upload_path, is_temp = _prepare_for_upload(path)
        try:
            result = cloudinary.uploader.upload(
                str(upload_path),
                public_id=public_id,
                resource_type=kind,
                overwrite=True,
                invalidate=True,
            )
        finally:
            if is_temp:
                try:
                    upload_path.unlink()
                    upload_path.parent.rmdir()
                except OSError:
                    pass  # best-effort cleanup

        manifest[path.name] = {
            "public_id": result["public_id"],
            "kind": kind,
            "sha256": digest,   # of the ORIGINAL, so re-edits re-upload
        }
        # Save after every successful upload, so a mid-loop failure preserves
        # everything uploaded so far.
        _save_manifest(manifest)
        uploaded += 1

    print(f"\nUploaded {uploaded} file(s). Manifest written to "
          f"{CLOUDINARY_MANIFEST.relative_to(ROOT)}.")


# ============================================================
# main
# ============================================================

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="Exit 1 if any output would change (for CI).")
    parser.add_argument("--upload", action="store_true",
                        help="Upload any new/changed files in talks/images+videos/ "
                             "to Cloudinary, then rebuild all pages.")
    args = parser.parse_args(argv)

    if args.upload:
        upload_command()
        print("\nRegenerating pages with updated Cloudinary URLs...")

    data = load_all()
    outputs = build_all(data)

    changed = []
    for relpath, content in outputs.items():
        target = ROOT / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        if existing != content:
            changed.append(relpath)
            if not args.check:
                target.write_text(content, encoding="utf-8")

    if args.check:
        if changed:
            print("Would rewrite:")
            for p in changed:
                print(f"  {p}")
            sys.exit(1)
        else:
            print("All pages up to date.")
            sys.exit(0)

    if changed:
        print(f"Rewrote {len(changed)} page(s):")
        for p in changed:
            print(f"  {p}")
    else:
        print("All pages already up to date.")


if __name__ == "__main__":
    main()
