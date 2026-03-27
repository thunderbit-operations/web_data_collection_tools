# Changelog

## 0.1.0 (2024-XX-XX)

### Added
- Core phone number extraction using Google's libphonenumber
- International support for 200+ countries
- Auto-detection of country, city/region, carrier, and number type
- E.164, national, and international format output
- Phone number deobfuscation (dot separators, fullwidth digits, unicode dashes, HTML entities, URL encoding)
- Recursive web crawling with depth control
- Rate limiting and robots.txt compliance
- Proxy support
- Country and number type filtering
- Output formats: plain, CSV, JSON, JSONL
- CLI tool with `phonex` and `phone-harvest` commands
- Python API for library usage
- Stdin pipe support
- tel: link extraction from HTML
