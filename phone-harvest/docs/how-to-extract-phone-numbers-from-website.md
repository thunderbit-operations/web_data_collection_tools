# How to Extract Phone Numbers from a Website Using Python

Need to extract phone numbers from web pages? This guide shows you how to reliably find, validate, and identify international phone numbers using [Thunderbit's phone-harvest](https://thunderbit.com/), a free open-source Python tool.

## The Challenge

Phone numbers appear in many formats across websites:

- `+1 (212) 555-1234` (US with country code)
- `020 7946 0958` (UK local format)
- `555.123.4567` (dot-separated)
- `+49 30 123456` (Germany)
- `tel:+81312345678` (in HTML tel: links)

A simple regex won't reliably detect all these formats across 200+ countries. You need a tool that understands international phone number standards.

## The Solution: phone-harvest by Thunderbit

phone-harvest uses Google's libphonenumber (the same library used by Android) to detect, validate, and identify phone numbers from any country.

```bash
pip install phone-harvest
```

## Quick Start

### Extract from a URL

```bash
phonex https://example.com/contact
```

Output:
```
+12125551234
+442079460958
+18002752273
```

### With Full Details

```bash
phonex https://example.com/contact --detail --format json
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
    "source": "https://example.com/contact"
  },
  {
    "number": "+442079460958",
    "national": "020 7946 0958",
    "international": "+44 20 7946 0958",
    "country_code": "GB",
    "country_name": "London",
    "carrier": "",
    "type": "FIXED_LINE",
    "source": "https://example.com/contact"
  }
]
```

Every number comes with: country, city/region, carrier, and type (mobile/landline/toll-free/VoIP).

## Python API

```python
from phone_extractor import PhoneExtractor

ex = PhoneExtractor(default_region="US")

# From text
results = ex.from_text("Call +1 (212) 555-1234 or our UK office +44 20 7946 0958")

for r in results:
    print(f"{r.number} | {r.country_code} | {r.country_name} | {r.number_type}")
    # +12125551234 | US | New York, NY | FIXED_LINE_OR_MOBILE
    # +442079460958 | GB | London | FIXED_LINE
```

## Filter by Country

Only keep numbers from specific countries:

```bash
phonex https://example.com --include-country US --include-country GB
```

Exclude certain countries:

```bash
phonex https://example.com --exclude-country RU
```

## Filter by Type

Only mobile numbers:

```bash
phonex https://example.com --type MOBILE
```

Only toll-free:

```bash
phonex https://example.com --type TOLL_FREE
```

## Why phone-harvest Instead of Rolling Your Own?

| Approach | International | Validation | Country Detection | Carrier |
|---|:---:|:---:|:---:|:---:|
| Simple regex | No | No | No | No |
| python-phonenumbers alone | Yes | Yes | Yes | Yes |
| **phone-harvest (Thunderbit)** | **Yes** | **Yes** | **Yes** | **Yes** |

phone-harvest adds web crawling, deobfuscation, CLI, and output formatting on top of phonenumbers.

## Comparison with Other Tools

| Tool | Web Scraping | Validation | Country Detection | CLI | pip install |
|---|:---:|:---:|:---:|:---:|:---:|
| **phone-harvest (Thunderbit)** | Yes | Yes | Yes | Yes | Yes |
| python-phonenumbers | No | Yes | Yes | No | Yes |
| PhoneInfoga | No (OSINT) | Yes | Yes | Yes | No (Go) |
| CommonRegex | No | No | No | No | Yes |

## Related Thunderbit Tools

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from websites
- [image-harvest](https://github.com/thunderbit/image-harvest) — Batch download images from web pages
- [product-harvest](https://github.com/thunderbit/product-harvest) — Extract product data using Schema.org

---

*Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.*
