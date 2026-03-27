# How to Extract Product Data from Any Website Without AI

Need to get product name, price, brand, and availability from ecommerce websites? This guide shows you how to do it without AI, CSS selectors, or site-specific rules — using structured data that sites already embed.

## The Secret: Schema.org Structured Data

Most ecommerce sites (Shopify, WooCommerce, BigCommerce, Amazon, and millions more) embed [Schema.org](https://schema.org/Product) structured data in their HTML. They add this for Google to understand their products for rich search results.

This data is already there. You just need to read it.

```html
<!-- Hidden in the HTML of most product pages: -->
<script type="application/ld+json">
{
  "@type": "Product",
  "name": "Wireless Headphones",
  "offers": {
    "price": "149.99",
    "priceCurrency": "USD",
    "availability": "InStock"
  },
  "brand": { "name": "ProMax" },
  "aggregateRating": { "ratingValue": "4.5", "reviewCount": "328" }
}
</script>
```

## The Tool: product-harvest by Thunderbit

[product-harvest](https://github.com/thunderbit/product-harvest) reads this structured data automatically. No AI, no API keys, no CSS selectors.

```bash
pip install product-harvest
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
    "url": "https://shop.example.com/headphones"
  }
]
```

## What Data Can You Extract?

| Field | Example | Source |
|---|---|---|
| Name | "Wireless Headphones" | JSON-LD, OG, Meta |
| Price | "149.99" | JSON-LD, OG, Meta |
| Currency | "USD" | JSON-LD, OG, Meta |
| Brand | "ProMax" | JSON-LD, OG |
| Availability | "InStock" | JSON-LD, OG |
| Rating | "4.5" | JSON-LD |
| Review count | "328" | JSON-LD |
| SKU | "WH-PM-2024" | JSON-LD |
| GTIN/EAN | "0123456789012" | JSON-LD |
| Category | "Electronics > Audio" | JSON-LD, OG |
| Description | Full product description | All methods |
| Image URL | Product image | JSON-LD, OG |

## Batch Processing

Extract from multiple product URLs:

```bash
productx url1 url2 url3 --format csv -o products.csv
```

From a file of URLs:

```bash
productx --file product-urls.txt --format csv -o products.csv
```

Pipe from another tool:

```bash
cat urls.txt | productx --stdin --format jsonl
```

## Python API

```python
from product_extractor import ProductExtractor

ex = ProductExtractor()

# Single URL
products = ex.from_url("https://shop.example.com/product")
for p in products:
    print(f"{p.name}: {p.currency} {p.price} ({p.brand})")
    print(f"  Rating: {p.rating}/5 ({p.review_count} reviews)")
    print(f"  Stock: {p.availability}")

# Batch URLs
products = ex.from_urls([
    "https://shop1.com/product-a",
    "https://shop2.com/product-b",
])

# Export as dictionary
for p in products:
    print(p.to_dict())
```

## Three Extraction Methods

product-harvest tries three methods in order of reliability:

1. **JSON-LD** — `<script type="application/ld+json">` with `@type: Product`. Most reliable, used by Shopify, WooCommerce, and most modern ecommerce platforms.

2. **Open Graph** — `<meta property="og:*">` and `<meta property="product:*">`. Used by Facebook Commerce and many sites.

3. **Meta tags + price regex** — Falls back to page title and price pattern matching for sites without structured data.

## Which Sites Have Structured Data?

Almost all ecommerce platforms embed it by default:

- Shopify stores — JSON-LD
- WooCommerce stores — JSON-LD
- BigCommerce — JSON-LD
- Amazon — JSON-LD
- eBay — JSON-LD
- Etsy — JSON-LD
- Most modern ecommerce sites

You can check any page: View Source → search for `application/ld+json`.

## Why Not Use AI?

| Approach | Accuracy | Speed | Cost | Maintenance |
|---|---|---|---|---|
| **product-harvest (Schema.org)** | High (structured data) | Fast | Free | Zero |
| AI/LLM extraction | High | Slow | API costs | Prompt tuning |
| CSS selector scraping | High | Fast | Free | Breaks when site changes |
| Regex scraping | Low | Fast | Free | Fragile |

product-harvest reads standardized data that sites maintain for Google. It doesn't break when they redesign their page because structured data is separate from visual layout.

## Related Thunderbit Tools

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from websites
- [phone-harvest](https://github.com/thunderbit/phone-harvest) — Extract phone numbers with country detection
- [image-harvest](https://github.com/thunderbit/image-harvest) — Batch download images from web pages

---

*Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.*
