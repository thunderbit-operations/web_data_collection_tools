# Web Data Collection Tools

> Open-source CLI tools for collecting data from web pages — by [Thunderbit](https://thunderbit.com/)

## Tools

| Tool | Description | CLI Command |
|------|-------------|-------------|
| [email-harvest](./email-harvest) | Extract email addresses from text, files, and web pages | `emx` |
| [phone-harvest](./phone-harvest) | Extract and identify phone numbers from text, files, and web pages | `phonex` |
| [image-harvest](./image-harvest) | Discover and batch download images from web pages | `imgx` |
| [product-harvest](./product-harvest) | Extract structured product data using Schema.org | `productx` |

## Common Features

- **Zero config** — works out of the box, no API keys needed
- **CLI-first** — pipe-friendly commands with Python API support
- **Recursive crawling** — follow links within a domain up to N levels deep
- **Multiple output formats** — plain text, CSV, JSON, JSONL
- **Polite crawling** — rate limiting and robots.txt compliance built-in
- **Proxy support** — route requests through HTTP/HTTPS proxies
- **Minimal dependencies** — Python 3.8+, mostly just `requests` + `beautifulsoup4`

## Quick Start

```bash
# Install any tool
pip install email-harvest
pip install phone-harvest
pip install image-harvest
pip install product-harvest

# Extract emails from a web page
emx https://example.com/contact

# Extract phone numbers
phonex https://example.com/contact

# Download all images
imgx https://example.com

# Extract product data
productx https://example.com/product
```

## License

[MIT](LICENSE)

---

Built by [Thunderbit](https://thunderbit.com/) — AI-powered web scraper and data extraction tools.
