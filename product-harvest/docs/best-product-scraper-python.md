# Best Product Scraper Tools for Python in 2024

A comparison of tools for extracting product data (prices, names, availability) from ecommerce websites.

## Quick Recommendation

- **No AI, no API keys, works on any site with Schema.org:** [product-harvest by Thunderbit](https://github.com/thunderbit/product-harvest)
- **AI-powered extraction from any HTML:** Crawl4AI (requires LLM API)
- **Amazon-specific scraping:** oxylabs/amazon-scraper (requires proxy API)

## The Approaches

### 1. Schema.org Parsing (product-harvest)

Reads the structured data that sites already embed for Google. No AI, no CSS selectors, no site-specific rules.

```bash
pip install product-harvest
productx https://shop.example.com/product --format json
```

**Pros:** Free, fast, zero config, doesn't break on redesigns.
**Cons:** Only works on sites with Schema.org data (most ecommerce sites have it).

### 2. AI/LLM Extraction (Crawl4AI, etc.)

Uses language models to understand page content and extract product fields.

**Pros:** Works on any page regardless of structure.
**Cons:** Requires API keys, costs money per request, slower.

### 3. CSS Selector Scraping (Scrapling, Scrapy)

Write per-site extraction rules targeting specific HTML elements.

**Pros:** Very accurate for known sites.
**Cons:** Breaks when sites change their HTML. Requires writing rules for each site.

### 4. Platform-Specific APIs (Oxylabs, etc.)

Commercial APIs that handle anti-bot, proxies, and parsing for specific platforms.

**Pros:** Handle anti-bot protection.
**Cons:** Paid service, platform-specific.

## Feature Matrix

| Feature | product-harvest | Crawl4AI | Scrapling | oxylabs |
|---|:---:|:---:|:---:|:---:|
| No AI/LLM needed | Yes | No | Yes | Yes |
| No API key | Yes | No | Yes | No |
| Any ecommerce site | Yes* | Yes | With rules | Platform-specific |
| Zero config | Yes | No | No | No |
| Price extraction | Yes | Yes | With rules | Yes |
| Brand/SKU/GTIN | Yes | Depends | With rules | Yes |
| Rating/reviews | Yes | Depends | With rules | Yes |
| Batch URLs | Yes | Yes | Yes | Yes |
| CSV/JSON output | Yes | Yes | Custom | JSON |
| pip install | Yes | Yes | Yes | No |
| Free | Yes | LLM costs | Yes | Paid |
| Dependencies | 2 | Many | Many | N/A |

*\*Requires Schema.org structured data — present on most ecommerce sites (Shopify, WooCommerce, Amazon, eBay, etc.)*

## Related Thunderbit Tools

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses
- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract phone numbers
- [image-harvest](https://github.com/thunderbit/image-harvest) — Batch download images

---

*Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.*
