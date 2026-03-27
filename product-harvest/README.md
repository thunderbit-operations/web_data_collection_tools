# product-harvest

> Extract structured product data from any web page using Schema.org — no AI required.

<!--
[![PyPI version](https://img.shields.io/pypi/v/product-harvest)](https://pypi.org/project/product-harvest/)
[![Python versions](https://img.shields.io/pypi/pyversions/product-harvest)](https://pypi.org/project/product-harvest/)
[![CI](https://github.com/thunderbit/product-harvest/actions/workflows/ci.yml/badge.svg)](https://github.com/thunderbit/product-harvest/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
-->

## Features

- **Zero config** — reads the structured data sites already embed for Google
- **Three extraction methods** — JSON-LD (preferred), Open Graph, and meta tag fallback
- **Rich product data** — name, price, currency, brand, SKU, GTIN, availability, rating, reviews, images, categories
- **Works with any ecommerce site** — Shopify, WooCommerce, BigCommerce, Amazon, and millions of sites using Schema.org
- **Batch processing** — extract from multiple URLs in one command
- **Multiple output formats** — plain text, CSV, JSON, JSONL
- **URL file input** — read URLs from a file or stdin pipe
- **No AI/LLM required** — pure parsing of existing structured data
- **Minimal dependencies** — only `requests` + `beautifulsoup4`

## How It Works

Most ecommerce sites embed [Schema.org](https://schema.org/Product) structured data in their HTML to help Google understand their products. product-harvest reads this existing data — no scraping rules, no CSS selectors, no AI needed.

```html
<!-- This is what sites already have in their HTML for Google: -->
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Wireless Headphones",
  "offers": { "price": "149.99", "priceCurrency": "USD" }
}
</script>
```

product-harvest just finds and parses it.

## Installation

```bash
pip install product-harvest
```

Requires Python 3.8+.

## Quick Start

Extract product data from a URL:

```bash
productx https://shop.example.com/product
```

Output:
```
ProMax Wireless Headphones    USD 149.99
```

With full details:

```bash
productx https://shop.example.com/product --detail --format json
```

```json
[
  {
    "name": "ProMax Wireless Headphones",
    "price": "149.99",
    "currency": "USD",
    "brand": "ProMax",
    "availability": "InStock",
    "rating": "4.5",
    "review_count": "328",
    "sku": "WH-PM-2024",
    "category": "Electronics > Audio > Headphones",
    "description": "Premium noise-cancelling wireless headphones...",
    "image": "https://shop.example.com/images/headphones.jpg",
    "url": "https://shop.example.com/headphones",
    "source_url": "https://shop.example.com/headphones",
    "extraction_method": "json-ld"
  }
]
```

Batch processing from a URL file:

```bash
productx --file product-urls.txt --format csv -o products.csv
```

Pipe URLs from another tool:

```bash
cat urls.txt | productx --stdin --format jsonl
```

## CLI Reference

```
productx [OPTIONS] URL...
```

### Input

| Flag | Description |
|------|-------------|
| `URL...` | Product page URLs (positional) |
| `--file, -F FILE` | Read URLs from file (one per line) |
| `--stdin` | Read URLs from stdin |

### Output

| Flag | Default | Description |
|------|---------|-------------|
| `--format, -f` | `plain` | Output: `plain`, `csv`, `json`, `jsonl` |
| `--output, -o FILE` | stdout | Write to file |
| `--detail, -d` | off | Include all fields |

### Fields Extracted

| Field | Source | Description |
|-------|--------|-------------|
| `name` | All methods | Product name |
| `price` | All methods | Price value |
| `currency` | All methods | Currency code (USD, EUR, etc.) |
| `brand` | JSON-LD, OG | Brand name |
| `availability` | JSON-LD, OG | InStock, OutOfStock, etc. |
| `rating` | JSON-LD | Average rating |
| `review_count` | JSON-LD | Number of reviews |
| `sku` | JSON-LD | Stock Keeping Unit |
| `gtin` | JSON-LD | Global Trade Item Number |
| `category` | JSON-LD, OG | Product category |
| `description` | All methods | Product description |
| `image` | JSON-LD, OG | Product image URL |
| `url` | All methods | Canonical product URL |

## Python API

```python
from product_extractor import ProductExtractor

ex = ProductExtractor()

# From URL
products = ex.from_url("https://shop.example.com/product")
for p in products:
    print(f"{p.name}: {p.currency} {p.price} ({p.brand})")

# From HTML string
products = ex.from_html(html_content, source_url="https://example.com")

# Batch URLs
products = ex.from_urls([
    "https://shop1.com/product-a",
    "https://shop2.com/product-b",
])

# Access all fields
p = products[0]
print(p.name, p.price, p.currency, p.brand, p.sku)
print(p.rating, p.review_count, p.availability)
print(p.to_dict())  # as dictionary
```

## Extraction Priority

product-harvest tries three methods in order and returns the first successful result:

1. **JSON-LD** (most reliable) — `<script type="application/ld+json">` with `@type: Product`
2. **Open Graph** — `<meta property="og:*">` and `<meta property="product:*">`
3. **Meta tags + price regex** (fallback) — page title + price pattern matching

## Comparison

| Feature | product-harvest | Crawl4AI | Scrapling | oxylabs/amazon-scraper |
|---------|:---:|:---:|:---:|:---:|
| No AI/LLM needed | Yes | No | Yes | Yes |
| No API key needed | Yes | Depends | Yes | No |
| Works on any site | Yes* | Yes | Yes | Amazon only |
| Zero config | Yes | No | No | No |
| Structured output | Yes | Yes | No | Yes |
| pip install | Yes | Yes | Yes | No |
| Dependencies | 2 | Many | Many | N/A |
| Price | Free | Free | Free | Paid proxy |

*\*Requires the site to have Schema.org or Open Graph product data.*

## Also by Thunderbit

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from text, files, and web pages
- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract and identify phone numbers from text, files, and web pages
- [image-harvest](https://github.com/thunderbit/image-harvest) — Discover and batch download images from web pages

## License

[MIT](LICENSE)

---

Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.
