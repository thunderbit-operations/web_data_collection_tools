# How to Download All Images from a Website Using Python

Need to batch download all images from a web page? This guide shows you how using [Thunderbit's image-harvest](https://thunderbit.com/), a free open-source Python tool that finds and downloads images with a single command.

## The Problem

Downloading images from websites manually is tedious. Right-clicking and saving each image one by one doesn't scale. You need a tool that can:

1. Find all images on a page (including lazy-loaded, srcset, and background images)
2. Filter out junk (tracking pixels, tiny icons)
3. Download them in parallel
4. Skip duplicates
5. Resume interrupted downloads

## The Solution: image-harvest by Thunderbit

```bash
pip install image-harvest
imgx https://example.com/gallery
```

That's it. All images are saved to `./images/`.

## Finding Images in All Locations

Most tools only check `<img src>` tags. image-harvest by Thunderbit finds images in 7 different locations:

| Source | Example | Other Tools |
|---|---|:---:|
| `<img src>` | Standard images | Yes |
| `<img data-src>` | Lazy-loaded images | No |
| `<img srcset>` | Responsive images | No |
| `<picture><source>` | Art direction | No |
| `<a href="*.jpg">` | Linked images | No |
| `<meta og:image>` | Open Graph images | No |
| CSS `background-image` | Background images | No |

This means image-harvest typically finds 2-3x more images than simple scrapers.

## Filtering Out Junk

By default, image-harvest automatically excludes:
- **Tracking pixels** (1x1 images)
- **Data URIs** (inline base64 images)
- **SVG icons** (toggleable with `--include-svg`)

You can also filter by:

```bash
# Only JPG and PNG, minimum 200px wide
imgx https://example.com --type jpg,png --min-width 200

# Skip files larger than 5MB
imgx https://example.com --max-size 5
```

## Parallel Downloads

Download 8 images simultaneously:

```bash
imgx https://example.com --workers 8
```

## Content Deduplication

Different URLs can point to the same image. image-harvest uses SHA-256 content hashing to detect and skip duplicates — even when URLs are different.

```bash
# Deduplication is on by default
imgx https://example.com

# Disable if needed
imgx https://example.com --no-dedupe
```

## Resume Support

If a download is interrupted, just run the same command again. Already-downloaded files are automatically skipped:

```bash
imgx https://example.com -o ./photos
# ... interrupted ...
imgx https://example.com -o ./photos  # continues where it left off
```

## Custom Renaming

Rename downloaded files sequentially:

```bash
imgx https://example.com --rename "{n:04d}.{ext}"
# Downloads as 0001.jpg, 0002.png, 0003.webp, ...
```

## List Images Without Downloading

Just want to see what's available?

```bash
imgx https://example.com --list-only
imgx https://example.com --list-only --list-format json
```

## Crawl an Entire Site

Find images across multiple pages:

```bash
imgx https://example.com --depth 2 --max-pages 100 -v
```

## Python API

```python
from image_extractor import ImageExtractor
from image_extractor.downloader import ImageDownloader

# Discover images
ex = ImageExtractor(min_width=100, include_types=["jpg", "png"])
images = ex.from_url("https://example.com/gallery")

print(f"Found {len(images)} images")
for img in images:
    print(f"  {img.url} ({img.filename})")

# Download them
dl = ImageDownloader(output_dir="./photos", workers=8)
stats = dl.download(images)
print(f"Downloaded {stats['downloaded']}, skipped {stats['skipped']}")
```

## Comparison with Other Tools

| Feature | image-harvest (Thunderbit) | gallery-dl | google-images-download |
|---|:---:|:---:|:---:|
| Any web page | Yes | Site-specific | Google only |
| Zero config | Yes | No | Yes |
| Parallel download | Yes | No | No |
| Content dedup | Yes | No | No |
| Resume support | Yes | Yes | No |
| Lazy-load detection | Yes | N/A | No |
| srcset/picture | Yes | N/A | No |
| og:image + CSS bg | Yes | No | No |
| Custom renaming | Yes | Yes | No |
| List-only mode | Yes | No | No |
| Dependencies | 2 | Many | Many |

## Related Thunderbit Tools

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from websites
- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract phone numbers with country detection
- [product-harvest](https://github.com/thunderbit/product-harvest) — Extract product data using Schema.org

---

*Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.*
