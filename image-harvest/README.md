# image-harvest

> A fast CLI tool to discover and batch download images from web pages.

<!--
[![PyPI version](https://img.shields.io/pypi/v/image-harvest)](https://pypi.org/project/image-harvest/)
[![Python versions](https://img.shields.io/pypi/pyversions/image-harvest)](https://pypi.org/project/image-harvest/)
[![CI](https://github.com/thunderbit/image-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/thunderbit/image-harvest/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
-->

## Features

- **Zero config** — `imgx https://example.com` downloads all images instantly
- **Smart discovery** — finds images in `<img>`, `data-src` (lazy-load), `srcset`, `<picture>`, `og:image`, CSS `background-image`, and `<a>` links
- **Parallel downloads** — configurable thread pool (default 4, up to 32)
- **Content deduplication** — skips duplicate images by SHA-256 hash, even from different URLs
- **Resume support** — automatically skips already-downloaded files
- **Size filtering** — skip by minimum width/height or maximum file size
- **Type filtering** — only download specific formats (jpg, png, webp, etc.)
- **Auto-excludes junk** — tracking pixels (1x1), data URIs, SVGs (toggleable)
- **Recursive crawling** — follow links to discover images across entire sites
- **Custom renaming** — rename files with patterns like `{n:04d}.{ext}`
- **List-only mode** — just discover and list image URLs without downloading
- **Multiple output formats** — plain, JSON, JSONL for list mode
- **Polite crawling** — rate limiting and robots.txt compliance
- **Proxy support** — route through HTTP/HTTPS proxies
- **Minimal dependencies** — only `requests` + `beautifulsoup4`

## Installation

```bash
pip install image-harvest
```

Requires Python 3.8+.

## Quick Start

Download all images from a page:

```bash
imgx https://example.com/gallery
```

Download only JPG and PNG, minimum 200px wide:

```bash
imgx https://example.com --type jpg,png --min-width 200 -o ./photos
```

Parallel download with 8 threads:

```bash
imgx https://example.com --workers 8
```

List images without downloading:

```bash
imgx https://example.com --list-only --list-format json
```

Crawl an entire site for images:

```bash
imgx https://example.com --depth 2 --max-pages 100 -v
```

Rename downloaded files sequentially:

```bash
imgx https://example.com --rename "{n:04d}.{ext}"
# Downloads as 0001.jpg, 0002.png, 0003.webp, ...
```

## CLI Reference

```
imgx [OPTIONS] URL...
```

### Output

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output DIR` | `./images` | Output directory |
| `--list-only` | off | Only list URLs, don't download |
| `--list-format` | `plain` | Format: `plain`, `json`, `jsonl` |

### Filtering

| Flag | Default | Description |
|------|---------|-------------|
| `--min-width PX` | `0` | Minimum image width (from HTML) |
| `--min-height PX` | `0` | Minimum image height (from HTML) |
| `--type EXT` | all | Only these types: `jpg,png,webp` |
| `--exclude-type EXT` | — | Exclude types: `gif,bmp` |
| `--include-svg` | off | Include SVG (excluded by default) |
| `--max-size MB` | `0` | Skip images larger than this |

### Download

| Flag | Default | Description |
|------|---------|-------------|
| `-w, --workers N` | `4` | Parallel download threads |
| `--overwrite` | off | Overwrite existing files |
| `--no-dedupe` | off | Disable content-hash deduplication |
| `--rename PATTERN` | — | Rename: `{n:04d}.{ext}`, `{name}_{n}.{ext}` |
| `--timeout SEC` | `30` | Download timeout per image |

### Crawling

| Flag | Default | Description |
|------|---------|-------------|
| `--depth N` | `0` | Recursion depth (0 = single page) |
| `--max-pages N` | `50` | Max pages to crawl |
| `--rate-limit SEC` | `1.0` | Seconds between page requests |
| `--ignore-robots` | off | Ignore robots.txt |
| `--proxy URL` | — | HTTP/HTTPS proxy |

## Python API

```python
from image_extractor import ImageExtractor
from image_extractor.downloader import ImageDownloader

# Discover images
ex = ImageExtractor(min_width=100, include_types=["jpg", "png"])
images = ex.from_url("https://example.com/gallery")

for img in images:
    print(f"{img.url} ({img.filename})")

# Download them
dl = ImageDownloader(output_dir="./photos", workers=8)
stats = dl.download(images)
print(f"Downloaded {stats['downloaded']} images")
```

### Crawling API

```python
from image_extractor import ImageExtractor
from image_extractor.crawler import ImageCrawler

ex = ImageExtractor()
crawler = ImageCrawler(ex, rate_limit=1.0)
images = crawler.crawl("https://example.com", max_depth=2)
```

## Image Discovery Sources

image-harvest looks for images in all these locations:

| Source | Example |
|--------|---------|
| `<img src>` | `<img src="/photo.jpg">` |
| `<img data-src>` | Lazy-loaded images |
| `<img srcset>` | Responsive images |
| `<picture><source>` | Art direction |
| `<a href>` | Links to image files |
| `<meta og:image>` | Open Graph images |
| CSS `background-image` | Inline style backgrounds |

Automatically excluded: tracking pixels (1x1), `data:` URIs, SVGs (unless `--include-svg`).

## Comparison

| Feature | image-harvest | gallery-dl | google-images-download | icrawler |
|---------|:---:|:---:|:---:|:---:|
| Zero config | Yes | No | Yes | No |
| Any web page | Yes | Site-specific | Google only | Search engines |
| Parallel downloads | Yes | No | No | Yes |
| Content deduplication | Yes | No | No | No |
| Resume support | Yes | Yes | No | No |
| Size/type filtering | Yes | Complex config | Basic | Basic |
| Lazy-load detection | Yes | N/A | No | No |
| srcset/picture | Yes | N/A | No | No |
| og:image + CSS bg | Yes | No | No | No |
| Recursive crawling | Yes | Per-site | No | No |
| Custom renaming | Yes | Yes | No | No |
| List-only mode | Yes | No | No | No |
| robots.txt | Yes | No | No | No |
| pip install | Yes | Yes | Yes | Yes |
| Dependencies | 2 | Many | Many | Several |

## Also by Thunderbit

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from text, files, and web pages
- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract and identify phone numbers from text, files, and web pages

## License

[MIT](LICENSE)

---

Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.
