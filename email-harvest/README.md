# email-harvest

> A fast, zero-config CLI tool to extract email addresses from text, files, and web pages.

<!--
[![PyPI version](https://img.shields.io/pypi/v/email-harvest)](https://pypi.org/project/email-harvest/)
[![Python versions](https://img.shields.io/pypi/pyversions/email-harvest)](https://pypi.org/project/email-harvest/)
[![CI](https://github.com/thunderbit/email-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/thunderbit/email-harvest/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/email-harvest)](https://pypi.org/project/email-harvest/)
-->

## Features

- **Extract from anywhere** — text strings, local files, URLs, or entire websites
- **Recursive crawling** — follow links within a domain up to N levels deep
- **Email deobfuscation** — decodes `[at]`, `(at)`, HTML entities (`&#64;`), URL encoding (`%40`), and more
- **Smart filtering** — auto-removes false positives (image filenames, placeholders, test domains)
- **Domain allow/block lists** — include or exclude specific email domains
- **Source tracking** — see which URL or file each email came from
- **Multiple output formats** — plain text, CSV, JSON, JSONL
- **Polite crawling** — rate limiting and robots.txt compliance built-in
- **Proxy support** — route requests through HTTP/HTTPS proxies
- **Pipe-friendly** — works with stdin/stdout for shell pipelines
- **Python API** — use as a library in your own scripts
- **Minimal dependencies** — only `requests` + `beautifulsoup4`

## Installation

```bash
pip install email-harvest
```

Requires Python 3.8+.

## Quick Start

Extract emails from a web page:

```bash
emx https://example.com/contact
```

Extract from a local file:

```bash
emx contacts.html
```

Extract from multiple files using glob patterns:

```bash
emx "pages/*.html" --format json
```

Pipe text through stdin:

```bash
curl -s https://example.com | emx -
```

Crawl an entire website (depth 2, max 100 pages):

```bash
emx https://example.com --depth 2 --max-pages 100 -v
```

## CLI Reference

```
emx [OPTIONS] SOURCE...
```

Sources are auto-detected:
- `https://...` or `http://...` → URL mode
- `-` → read from stdin
- `*.html` → glob pattern
- anything else → file path

### Crawling Options

| Flag | Default | Description |
|------|---------|-------------|
| `--depth N` | `0` | Recursion depth for URLs (0 = single page) |
| `--max-pages N` | `50` | Maximum pages to crawl per URL |
| `--rate-limit SEC` | `1.0` | Seconds between requests |
| `--ignore-robots` | off | Ignore robots.txt restrictions |
| `--proxy URL` | — | HTTP/HTTPS proxy |
| `--timeout SEC` | `10` | Request timeout |
| `--user-agent STR` | `EmailHarvest/1.0` | Custom User-Agent |

### Filtering Options

| Flag | Description |
|------|-------------|
| `--include-domain DOMAIN` | Only keep emails from this domain (repeatable) |
| `--exclude-domain DOMAIN` | Exclude emails from this domain (repeatable) |
| `--no-deobfuscate` | Disable email deobfuscation |

### Output Options

| Flag | Default | Description |
|------|---------|-------------|
| `--format, -f` | `plain` | Output format: `plain`, `csv`, `json`, `jsonl` |
| `--output, -o FILE` | stdout | Write to file |
| `--with-source` | off | Show source URL/file for each email |
| `--sort` | off | Sort alphabetically |
| `--count` | off | Print only the count |
| `-v, --verbose` | off | Show progress on stderr |
| `-q, --quiet` | off | Suppress all non-output messages |

## Output Examples

**Plain (default):**
```
alice@company.com
bob@company.com
```

**JSON:**
```bash
emx page.html --format json
```
```json
[
  "alice@company.com",
  "bob@company.com"
]
```

**CSV with source tracking:**
```bash
emx https://example.com --format csv --with-source
```
```csv
email,source,source_type
alice@company.com,https://example.com/contact,url
bob@company.com,https://example.com/about,url
```

**JSONL (streaming):**
```bash
emx page.html --format jsonl
```
```
{"email": "alice@company.com"}
{"email": "bob@company.com"}
```

## Python API

```python
from email_extractor import EmailExtractor

ex = EmailExtractor()

# From text
emails = ex.from_text("Contact us at hello@company.org")
# ['hello@company.org']

# From file
emails = ex.from_file("contacts.html")

# From HTML with mailto: detection
emails = ex.from_html("<a href='mailto:hi@co.org'>Email us</a>")

# From glob pattern
emails = ex.from_glob("pages/**/*.html")

# With source tracking
results = ex.extract("hi@co.org", source="input.txt", source_type="file")
for r in results:
    print(f"{r.email} from {r.source}")

# With domain filtering
ex = EmailExtractor(
    include_domains=["company.org"],
    exclude_domains=["spam.org"],
)

# Disable deobfuscation
ex = EmailExtractor(use_deobfuscate=False)
```

### Web Crawling API

```python
from email_extractor import EmailExtractor
from email_extractor.crawler import WebCrawler

ex = EmailExtractor()
crawler = WebCrawler(
    extractor=ex,
    rate_limit=1.0,
    respect_robots=True,
)

# Single page
results = crawler.extract_url("https://example.com/contact")

# Recursive crawl
results = crawler.crawl("https://example.com", max_depth=2, max_pages=100)

for r in results:
    print(f"{r.email} (found on {r.source})")
```

## Email Deobfuscation

email-harvest automatically detects and decodes common email obfuscation patterns:

| Obfuscated | Decoded |
|------------|---------|
| `user [at] domain [dot] com` | `user@domain.com` |
| `user (at) domain (dot) com` | `user@domain.com` |
| `user {at} domain {dot} com` | `user@domain.com` |
| `user AT domain DOT com` | `user@domain.com` |
| `user &#64; domain &#46; com` | `user@domain.com` |
| `user%40domain.com` | `user@domain.com` |
| `user @ domain . com` | `user@domain.com` |

Disable with `--no-deobfuscate` (CLI) or `use_deobfuscate=False` (API).

## Comparison

| Feature | email-harvest | extract-emails | emailfinder |
|---------|:---:|:---:|:---:|
| CLI tool | Yes | No | Yes |
| Python API | Yes | Yes | Yes |
| URL extraction | Yes | Yes | Yes |
| Recursive crawling | Yes | No | No |
| Email deobfuscation | Yes | No | No |
| False positive filtering | Yes | No | No |
| Source tracking | Yes | No | No |
| JSON/CSV/JSONL output | Yes | No | No |
| robots.txt compliance | Yes | No | No |
| Rate limiting | Yes | No | No |
| Proxy support | Yes | No | No |
| stdin pipe support | Yes | No | No |
| Zero config | Yes | No | No |

## Development

```bash
git clone https://github.com/thunderbit/email-harvest.git
cd email-harvest
pip install -e ".[dev]"
pytest
```

## Also by Thunderbit

- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract and identify phone numbers from text, files, and web pages
- [image-harvest](https://github.com/thunderbit/image-harvest) — Discover and batch download images from web pages
- [product-harvest](https://github.com/thunderbit/product-harvest) — Extract structured product data using Schema.org

## License

[MIT](LICENSE)

---

Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.
