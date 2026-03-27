"""Command-line interface for product-harvest."""

import argparse
import sys
from typing import List, Optional

from product_extractor import __version__
from product_extractor.extractor import ProductExtractor
from product_extractor.formatters import FORMATTERS, format_results


def _progress(msg: str, verbose: bool = True) -> None:
    if verbose and sys.stderr.isatty():
        print(f"\033[90m{msg}\033[0m", file=sys.stderr, flush=True)
    elif verbose:
        print(msg, file=sys.stderr, flush=True)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="productx",
        description="Extract structured product data from web pages using Schema.org.",
        epilog="Examples:\n"
        "  productx https://shop.example.com/product\n"
        "  productx url1 url2 url3 --format csv --detail\n"
        "  productx --file urls.txt --format json\n"
        "  cat urls.txt | productx --stdin --format jsonl\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("urls", nargs="*", metavar="URL",
                        help="product page URLs")
    parser.add_argument("--file", "-F", metavar="FILE",
                        help="read URLs from file (one per line)")
    parser.add_argument("--stdin", action="store_true",
                        help="read URLs from stdin")

    out = parser.add_argument_group("output")
    out.add_argument("--format", "-f", choices=list(FORMATTERS.keys()),
                     default="plain", dest="output_format",
                     help="output format (default: plain)")
    out.add_argument("--output", "-o", metavar="FILE",
                     help="write to file instead of stdout")
    out.add_argument("--detail", "-d", action="store_true",
                     help="include all fields (description, image, sku, etc.)")

    parser.add_argument("--timeout", type=int, default=10,
                        help="request timeout (default: 10)")
    parser.add_argument("--user-agent", default="ProductHarvest/1.0",
                        help="custom User-Agent")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show progress on stderr")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="suppress non-output messages")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    verbose = args.verbose and not args.quiet

    # Collect URLs
    urls: List[str] = list(args.urls or [])

    if args.file:
        try:
            with open(args.file) as f:
                urls.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))
        except FileNotFoundError:
            print(f"productx: error: file not found: {args.file}", file=sys.stderr)
            return 2

    if args.stdin or (not urls and not sys.stdin.isatty()):
        urls.extend(line.strip() for line in sys.stdin if line.strip() and not line.startswith("#"))

    if not urls:
        parser.print_help(sys.stderr)
        return 2

    extractor = ProductExtractor(timeout=args.timeout, user_agent=args.user_agent)

    all_products = []
    try:
        for url in urls:
            _progress(f"Fetching {url}...", verbose)
            try:
                products = extractor.from_url(url)
                all_products.extend(products)
                if products:
                    _progress(f"  Found {len(products)} product(s)", verbose)
                else:
                    _progress(f"  No product data found", verbose)
            except Exception as e:
                _progress(f"  Error: {e}", verbose)
    except KeyboardInterrupt:
        print("\nproductx: interrupted", file=sys.stderr)
        return 130

    if not all_products:
        if not args.quiet:
            print("productx: no product data found", file=sys.stderr)
        return 1

    output = format_results(all_products, fmt=args.output_format, detail=args.detail)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        if not args.quiet:
            _progress(f"Wrote {len(all_products)} product(s) to {args.output}", verbose=True)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
