# Talks / Judging — media assets (images and videos)

Drop all talk / judging media here — photos, slide screenshots, and short video clips. Each card can contain **any mix** of images and videos, and multiple items per card auto-render as a swipeable carousel with dot indicators + "N / M" counter.

## Naming convention

- **Images:** `talk-<slug>-<n>.jpg` (or `.png`, `.webp`)
- **Videos:** `talk-<slug>-<n>.mp4` (or `.webm`, `.mov`)

Examples:
```
talk-famelab-2016-1.jpg
talk-nasiko-akamai-1.jpg
talk-nasiko-akamai-2.jpg
talk-nasiko-akamai-clip.mp4
judge-somehack-2024-1.jpg
```

## Recommended specs

### Images
- Aspect ratio: **16 : 9** (non-16:9 media gets center-cropped)
- Resolution: 1600 × 900 px ideal, 1200 × 675 minimum
- File size: under ~300 KB (compress via https://squoosh.app)
- Format: `.jpg` for photos, `.png` for slides/screenshots

### Videos
- Aspect ratio: **16 : 9**
- Duration: keep short — ~30 s max for a personal-site clip
- File size: under **~15 MB** (GitHub has a 100 MB per-file hard cap; big videos should be uploaded to YouTube and linked via the `video:` URL field in `details.txt` instead of embedded here)
- Format: `.mp4` (H.264 + AAC) is the safest for browser support
- Compress with `ffmpeg -i in.mov -vcodec libx264 -crf 24 -preset slow -acodec aac -movflags +faststart out.mp4`

## How they appear on the page

- On page load, the small script at the bottom of `/talks/index.html` scans each card's `.talk-gallery-track` for `<img>` and `<video>` children — both are treated as slides.
- Videos show their first frame as a poster (via `preload="metadata"`), with native browser controls when clicked/tapped.
- Images and videos can be interleaved in any order within a single card.

## Live URLs

Once pushed to GitHub, files are accessible at:

```
https://suranjangoswami.com/talks/images+videos/<filename>
```

Example: `https://suranjangoswami.com/talks/images+videos/talk-nasiko-akamai-1.jpg`

## How they're referenced

You don't reference them directly in HTML — instead, list filenames in the `media:` field of each entry in `/Users/suranjan/code/suranjangoswami.com/talks/details.txt`:

```
media: talk-nasiko-akamai-1.jpg, talk-nasiko-akamai-2.jpg, talk-nasiko-akamai-clip.mp4
```

The site's build (when you say "sync talks" to Claude) turns each filename into the correct `<img>` or `<video>` tag automatically based on the file extension.
