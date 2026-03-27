"""Command-line interface for phone-harvest."""

import argparse
import sys
from typing import List, Optional

from phone_extractor import __version__
from phone_extractor.crawler import WebCrawler
from phone_extractor.extractor import PhoneExtractor
from phone_extractor.formatters import FORMATTERS, format_results
from phone_extractor.utils import (
    ResultSet,
    detect_stdin,
    expand_glob,
    is_glob,
    is_url,
    progress,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="phonex",
        description="Extract phone numbers from text, files, and web pages.",
        epilog="Examples:\n"
        "  phonex https://example.com/contact\n"
        "  phonex page.html contacts.txt\n"
        "  phonex https://example.com --detail --format json\n"
        "  echo '+1 555-123-4567' | phonex -\n"
        "  phonex https://example.com --depth 2 --region GB\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "sources",
        nargs="*",
        metavar="SOURCE",
        help="URLs, file paths, glob patterns, or - for stdin",
    )

    # Region / parsing
    region = parser.add_argument_group("region")
    region.add_argument(
        "--region", "-r",
        default="US",
        metavar="CODE",
        help="default country for local numbers, ISO 3166-1 alpha-2 (default: US)",
    )

    # Crawling
    crawl = parser.add_argument_group("crawling")
    crawl.add_argument("--depth", type=int, default=0,
                       help="recursion depth for URLs (default: 0)")
    crawl.add_argument("--max-pages", type=int, default=50,
                       help="max pages to crawl per URL (default: 50)")
    crawl.add_argument("--rate-limit", type=float, default=1.0,
                       help="seconds between requests (default: 1.0)")
    crawl.add_argument("--ignore-robots", action="store_true",
                       help="ignore robots.txt restrictions")
    crawl.add_argument("--proxy", help="HTTP/HTTPS proxy URL")
    crawl.add_argument("--timeout", type=int, default=10,
                       help="request timeout in seconds (default: 10)")
    crawl.add_argument("--user-agent", default="PhoneHarvest/1.0",
                       help="custom User-Agent string")

    # Filtering
    filt = parser.add_argument_group("filtering")
    filt.add_argument("--include-country", action="append", metavar="CODE",
                      help="only keep numbers from this country (repeatable)")
    filt.add_argument("--exclude-country", action="append", metavar="CODE",
                      help="exclude numbers from this country (repeatable)")
    filt.add_argument("--type", action="append", metavar="TYPE",
                      dest="include_type",
                      help="only keep this type: MOBILE, FIXED_LINE, VOIP, TOLL_FREE (repeatable)")
    filt.add_argument("--no-deobfuscate", action="store_true",
                      help="disable phone number deobfuscation")

    # Output
    out = parser.add_argument_group("output")
    out.add_argument("--format", "-f", choices=list(FORMATTERS.keys()),
                     default="plain", dest="output_format",
                     help="output format (default: plain)")
    out.add_argument("--output", "-o", metavar="FILE",
                     help="write output to file instead of stdout")
    out.add_argument("--detail", "-d", action="store_true",
                     help="include country, carrier, type, and source info")
    out.add_argument("--sort", action="store_true",
                     help="sort output alphabetically")
    out.add_argument("--count", action="store_true",
                     help="print only the count")
    out.add_argument("--national", action="store_true",
                     help="output in national format instead of E.164")

    # Verbosity
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show progress on stderr")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="suppress all non-output messages")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    return parser


def _process_sources(
    sources: List[str],
    extractor: PhoneExtractor,
    crawler: WebCrawler,
    args: argparse.Namespace,
) -> ResultSet:
    result_set = ResultSet()
    verbose = args.verbose and not args.quiet

    for source in sources:
        if source == "-":
            progress("Reading from stdin...", verbose)
            text = sys.stdin.read()
            results = extractor.from_text(text, source="stdin", source_type="stdin")
            result_set.add_many(results)
            progress(f"  Found {len(results)} number(s) from stdin", verbose)

        elif is_url(source):
            if args.depth > 0:
                progress(
                    f"Crawling {source} (depth={args.depth}, max={args.max_pages})...",
                    verbose,
                )
                results = crawler.crawl(source, max_depth=args.depth, max_pages=args.max_pages)
            else:
                progress(f"Fetching {source}...", verbose)
                results = crawler.extract_url(source)
            result_set.add_many(results)
            progress(f"  Found {len(results)} number(s) from {source}", verbose)

        elif is_glob(source):
            files = expand_glob(source)
            progress(f"Processing {len(files)} file(s) matching {source!r}...", verbose)
            for filepath in files:
                results = extractor.from_file(filepath)
                result_set.add_many(results)
            progress(f"  Found {len(result_set)} unique number(s)", verbose)

        else:
            progress(f"Reading {source}...", verbose)
            try:
                results = extractor.from_file(source)
                result_set.add_many(results)
                progress(f"  Found {len(results)} number(s) from {source}", verbose)
            except FileNotFoundError:
                print(f"phonex: error: file not found: {source}", file=sys.stderr)
            except PermissionError:
                print(f"phonex: error: permission denied: {source}", file=sys.stderr)

    return result_set


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    sources = args.sources or []
    if not sources and detect_stdin():
        sources = ["-"]
    if not sources:
        parser.print_help(sys.stderr)
        return 2

    extractor = PhoneExtractor(
        default_region=args.region,
        include_countries=args.include_country,
        exclude_countries=args.exclude_country,
        include_types=args.include_type,
        use_deobfuscate=not args.no_deobfuscate,
    )

    verbose = args.verbose and not args.quiet

    def on_page_done(url: str, pages_done: int, found: int) -> None:
        progress(f"  [{pages_done} pages] {url} ({found} numbers so far)", verbose)

    crawler = WebCrawler(
        extractor=extractor,
        rate_limit=args.rate_limit,
        respect_robots=not args.ignore_robots,
        proxy=args.proxy,
        timeout=args.timeout,
        user_agent=args.user_agent,
        on_page_done=on_page_done if verbose else None,
    )

    try:
        result_set = _process_sources(sources, extractor, crawler, args)
    except KeyboardInterrupt:
        print("\nphonex: interrupted", file=sys.stderr)
        return 130

    if args.count:
        print(len(result_set))
        return 0 if len(result_set) > 0 else 1

    results = result_set.results()
    if not results:
        if not args.quiet:
            print("phonex: no phone numbers found", file=sys.stderr)
        return 1

    if args.sort:
        results.sort(key=lambda r: r.number)

    # Override number field to national format if requested
    if args.national:
        for r in results:
            r.number = r.national

    output = format_results(results, fmt=args.output_format, detail=args.detail)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        if not args.quiet:
            progress(f"Wrote {len(results)} number(s) to {args.output}", verbose=True)
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
