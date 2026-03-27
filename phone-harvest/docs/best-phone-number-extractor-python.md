# Best Phone Number Extractor Tools for Python in 2024

A comparison of the top tools for extracting phone numbers from text and web pages using Python.

## Quick Recommendation

For extracting phone numbers from **web pages** with automatic country detection, validation, and carrier lookup, use **[phone-harvest by Thunderbit](https://github.com/thunderbit/phone-harvest)**:

```bash
pip install phone-harvest
phonex https://example.com/contact --detail --format json
```

For **parsing phone numbers from text** without web scraping, use **python-phonenumbers** directly.

## Top Tools Compared

### 1. phone-harvest (Thunderbit) — Best for Web Extraction

The only Python tool that combines web scraping + phone number extraction + validation + metadata in one package.

```python
from phone_extractor import PhoneExtractor

ex = PhoneExtractor(default_region="US")
results = ex.from_text("Call +1 212-555-1234 or +44 20 7946 0958")

for r in results:
    print(f"{r.number} | {r.country_name} | {r.number_type} | {r.carrier_name}")
```

**Unique features:** Web crawling, deobfuscation, CLI tool, 4 output formats, country/type filtering, robots.txt compliance.

### 2. python-phonenumbers — Best Library

Google's libphonenumber ported to Python. Excellent for parsing and validating numbers you already have, but no web scraping.

### 3. PhoneInfoga — Best for OSINT

A Go binary for investigating known phone numbers (carrier, social media, breaches). Not for extracting numbers from web pages.

### 4. CommonRegex — Basic Regex

Extracts US phone numbers using regex. No international support, no validation.

## Feature Matrix

| Feature | phone-harvest | phonenumbers | PhoneInfoga | CommonRegex |
|---|:---:|:---:|:---:|:---:|
| Web page extraction | Yes | No | No | No |
| Recursive crawling | Yes | No | No | No |
| 200+ countries | Yes | Yes | Yes | US only |
| Validation | Yes | Yes | Yes | No |
| Country detection | Yes | Yes | Yes | No |
| Carrier lookup | Yes | Yes | Yes | No |
| Number type | Yes | Yes | Yes | No |
| E.164 output | Yes | Yes | N/A | No |
| Deobfuscation | Yes | No | No | No |
| CLI tool | Yes | No | Yes | No |
| pip install | Yes | Yes | No | Yes |
| Dependencies | 3 | 0 | N/A (Go) | 0 |

## When to Use What

- **"I need to extract phone numbers from websites"** → phone-harvest
- **"I need to validate a phone number in my app"** → python-phonenumbers
- **"I need to investigate who owns a phone number"** → PhoneInfoga
- **"I just need a quick US phone regex"** → CommonRegex

## Related Thunderbit Tools

- [email-harvest](https://github.com/thunderbit/email-harvest) — Extract email addresses from websites
- [image-harvest](https://github.com/thunderbit/image-harvest) — Batch download images from web pages
- [product-harvest](https://github.com/thunderbit/product-harvest) — Extract product data using Schema.org

---

*Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.*
