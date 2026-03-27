# phone-harvest

> A fast CLI tool to extract, validate, and identify phone numbers from text, files, and web pages.

<!--
[![PyPI version](https://img.shields.io/pypi/v/phone-harvest)](https://pypi.org/project/phone-harvest/)
[![Python versions](https://img.shields.io/pypi/pyversions/phone-harvest)](https://pypi.org/project/phone-harvest/)
[![CI](https://github.com/thunderbit/phone-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/thunderbit/phone-harvest/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
-->

## Features

- **Extract from anywhere** — text strings, local files, URLs, or entire websites
- **International support** — recognizes phone numbers from 200+ countries using Google's libphonenumber
- **Auto-identify** — detects country, city/region, carrier, and number type (mobile/landline/toll-free/VoIP)
- **E.164 normalization** — outputs all numbers in standardized `+15551234567` format
- **Number deobfuscation** — handles dot-separated (`555.123.4567`), fullwidth digits, unicode dashes, HTML entities
- **Smart validation** — rejects fake/invalid numbers using Google's phone number database
- **Recursive crawling** — follow links within a domain up to N levels deep
- **Polite crawling** — rate limiting and robots.txt compliance built-in
- **Country/type filtering** — include or exclude by country code or number type
- **Multiple output formats** — plain text, CSV, JSON, JSONL with full metadata
- **Proxy support** — route requests through HTTP/HTTPS proxies
- **Pipe-friendly** — works with stdin/stdout for shell pipelines
- **Python API** — use as a library in your own scripts

## Installation

```bash
pip install phone-harvest
```

Requires Python 3.8+. Only 3 dependencies: `requests`, `beautifulsoup4`, `phonenumbers`.

## Quick Start

Extract phone numbers from a web page:

```bash
phonex https://example.com/contact
```

With full details (country, carrier, type):

```bash
phonex https://example.com/contact --detail
```

Output:
```
+12125551234  US  FIXED_LINE_OR_MOBILE  New York, NY  stdin
+442079460958  GB  FIXED_LINE  London  stdin
```

Extract from a local file:

```bash
phonex contacts.html --format json --detail
```

```json
[
  {
    "number": "+12125551234",
    "national": "(212) 555-1234",
    "international": "+1 212-555-1234",
    "country_code": "US",
    "country_name": "New York, NY",
    "carrier": "",
    "type": "FIXED_LINE_OR_MOBILE",
    "source": "contacts.html"
  }
]
```

Pipe text through stdin:

```bash
echo "Call +44 20 7946 0958 or +1 212-555-1234" | phonex -
```

Crawl an entire website:

```bash
phonex https://example.com --depth 2 --max-pages 100 -v
```

## CLI Reference

```
phonex [OPTIONS] SOURCE...
```

### Region

| Flag | Default | Description |
|------|---------|-------------|
| `--region, -r CODE` | `US` | Default country for local numbers (ISO 3166-1) |

### Crawling Options

| Flag | Default | Description |
|------|---------|-------------|
| `--depth N` | `0` | Recursion depth for URLs (0 = single page) |
| `--max-pages N` | `50` | Maximum pages to crawl per URL |
| `--rate-limit SEC` | `1.0` | Seconds between requests |
| `--ignore-robots` | off | Ignore robots.txt restrictions |
| `--proxy URL` | — | HTTP/HTTPS proxy |
| `--timeout SEC` | `10` | Request timeout |

### Filtering Options

| Flag | Description |
|------|-------------|
| `--include-country CODE` | Only keep numbers from this country (repeatable) |
| `--exclude-country CODE` | Exclude numbers from this country (repeatable) |
| `--type TYPE` | Only keep: MOBILE, FIXED_LINE, TOLL_FREE, VOIP (repeatable) |
| `--no-deobfuscate` | Disable number deobfuscation |

### Output Options

| Flag | Default | Description |
|------|---------|-------------|
| `--format, -f` | `plain` | Output format: `plain`, `csv`, `json`, `jsonl` |
| `--output, -o FILE` | stdout | Write to file |
| `--detail, -d` | off | Include country, carrier, type, source |
| `--national` | off | Output in national format instead of E.164 |
| `--sort` | off | Sort alphabetically |
| `--count` | off | Print only the count |

## Python API

```python
from phone_extractor import PhoneExtractor

ex = PhoneExtractor(default_region="US")

# From text
results = ex.from_text("Call +1 (212) 555-1234 or +44 20 7946 0958")
for r in results:
    print(f"{r.number} | {r.country_code} | {r.country_name} | {r.number_type}")
    # +12125551234 | US | New York, NY | FIXED_LINE_OR_MOBILE
    # +442079460958 | GB | London | FIXED_LINE

# Just the numbers
numbers = ex.extract_simple("Call +1 212-555-1234")
# ['+12125551234']

# From file
results = ex.from_file("contacts.html")

# From HTML with tel: link detection
results = ex.from_html("<a href='tel:+12125551234'>Call</a>")

# With country filtering
ex = PhoneExtractor(
    default_region="US",
    include_countries=["US", "GB"],
    exclude_countries=["RU"],
    include_types=["MOBILE"],
)
```

### Web Crawling API

```python
from phone_extractor import PhoneExtractor
from phone_extractor.crawler import WebCrawler

ex = PhoneExtractor(default_region="US")
crawler = WebCrawler(ex, rate_limit=1.0, respect_robots=True)

# Single page
results = crawler.extract_url("https://example.com/contact")

# Recursive crawl
results = crawler.crawl("https://example.com", max_depth=2, max_pages=100)

for r in results:
    print(f"{r.number} ({r.country_name}) found on {r.source}")
```

## Phone Number Deobfuscation

phone-harvest automatically normalizes common obfuscation patterns:

| Obfuscated | Normalized |
|------------|-----------|
| `555.123.4567` | `555-123-4567` |
| `555 dash 123 dash 4567` | `555-123-4567` |
| `&#43;1 212 555 1234` | `+1 212 555 1234` |
| `%2B1 212 555 1234` | `+1 212 555 1234` |
| Fullwidth digits `５５５` | `555` |
| Unicode dashes `555–123–4567` | `555-123-4567` |
| Non-breaking spaces | Regular spaces |

## Comparison

| Feature | phone-harvest | python-phonenumbers | PhoneInfoga | CommonRegex |
|---------|:---:|:---:|:---:|:---:|
| CLI tool | Yes | No | Yes (Go) | No |
| Python API | Yes | Yes | No | Yes |
| Web page extraction | Yes | No | No | No |
| Recursive crawling | Yes | No | No | No |
| International support | 200+ countries | 200+ countries | Yes | US-only |
| Country detection | Yes | Yes | Yes | No |
| Carrier lookup | Yes | Yes | Yes | No |
| Number type (mobile/landline) | Yes | Yes | Yes | No |
| E.164 normalization | Yes | Yes | N/A | No |
| Number validation | Yes | Yes | Yes | No |
| Deobfuscation | Yes | No | No | No |
| robots.txt compliance | Yes | N/A | N/A | N/A |
| JSON/CSV output | Yes | No | JSON | No |
| stdin pipe support | Yes | No | No | No |
| pip install | Yes | Yes | No | Yes |

## Development

```bash
git clone https://github.com/thunderbit/phone-harvest.git
cd phone-harvest
pip install -e ".[dev]"
pytest
```

## Also by Thunderbit

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from text, files, and web pages
- [image-harvest](https://github.com/thunderbit/image-harvest) — Discover and batch download images from web pages
- [product-harvest](https://github.com/thunderbit/product-harvest) — Extract structured product data using Schema.org

## License

[MIT](LICENSE)

---

Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.
