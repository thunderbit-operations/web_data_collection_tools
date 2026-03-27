"""Command-line interface for email-harvest."""

import argparse
import sys
from typing import List, Optional

from email_extractor import __version__
from email_extractor.crawler import WebCrawler
from email_extractor.extractor import EmailExtractor
from email_extractor.formatters import FORMATTERS, format_results
from email_extractor.utils import (
    EmailResult,
    ResultSet,
    detect_stdin,
    expand_glob,
    is_glob,
    is_url,
    progress,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="emx",
        description="Extract email addresses from text, files, and web pages.",
        epilog="Examples:\n"
        "  emx https://example.com/contact\n"
        "  emx page.html contacts.txt\n"
        '  emx "*.html" --format json\n'
        "  echo 'hi@world.com' | emx -\n"
        "  emx https://example.com --depth 2 --max-pages 100\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "sources",
        nargs="*",
        metavar="SOURCE",
        help="URLs, file paths, glob patterns, or - for stdin",
    )

    # Crawling options
    crawl = parser.add_argument_group("crawling")
    crawl.add_argument(
        "--depth",
        type=int,
        default=0,
        help="recursion depth for URLs (default: 0, single page)",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="max pages to crawl per URL (default: 50)",
    )
    crawl.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="seconds between requests (default: 1.0)",
    )
    crawl.add_argument(
        "--ignore-robots",
        action="store_true",
        help="ignore robots.txt restrictions",
    )
    crawl.add_argument("--proxy", help="HTTP/HTTPS proxy URL")
    crawl.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="request timeout in seconds (default: 10)",
    )
    crawl.add_argument("--user-agent", default="EmailHarvest/1.0", help="custom User-Agent string")

    # Filtering options
    filt = parser.add_argument_group("filtering")
    filt.add_argument(
        "--include-domain",
        action="append",
        metavar="DOMAIN",
        help="only keep emails from this domain (repeatable)",
    )
    filt.add_argument(
        "--exclude-domain",
        action="append",
        metavar="DOMAIN",
        help="exclude emails from this domain (repeatable)",
    )
    filt.add_argument(
        "--no-deobfuscate",
        action="store_true",
        help="disable email deobfuscation",
    )

    # Output options
    out = parser.add_argument_group("output")
    out.add_argument(
        "--format",
        "-f",
        choices=list(FORMATTERS.keys()),
        default="plain",
        dest="output_format",
        help="output format (default: plain)",
    )
    out.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="write output to file instead of stdout",
    )
    out.add_argument(
        "--with-source",
        action="store_true",
        help="include source URL/file for each email",
    )
    out.add_argument(
        "--sort",
        action="store_true",
        help="sort output alphabetically",
    )
    out.add_argument(
        "--count",
        action="store_true",
        help="print only the count of unique emails found",
    )

    # Verbosity
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="show progress and debug info on stderr",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress all non-output messages",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def _process_sources(
    sources: List[str],
    extractor: EmailExtractor,
    crawler: WebCrawler,
    args: argparse.Namespace,
) -> ResultSet:
    """Process all input sources and collect results."""
    result_set = ResultSet()
    verbose = args.verbose and not args.quiet

    for source in sources:
        if source == "-":
            # Read from stdin
            progress("Reading from stdin...", verbose)
            text = sys.stdin.read()
            results = extractor.extract(text, source="stdin", source_type="stdin")
            result_set.add_many(results)
            progress(f"  Found {len(results)} email(s) from stdin", verbose)

        elif is_url(source):
            # URL source
            if args.depth > 0:
                progress(
                    f"Crawling {source} (depth={args.depth}, max={args.max_pages})...",
                    verbose,
                )
                results = crawler.crawl(
                    source,
                    max_depth=args.depth,
                    max_pages=args.max_pages,
                )
            else:
                progress(f"Fetching {source}...", verbose)
                results = crawler.extract_url(source)
            result_set.add_many(results)
            progress(f"  Found {len(results)} email(s) from {source}", verbose)

        elif is_glob(source):
            # Glob pattern
            files = expand_glob(source)
            progress(f"Processing {len(files)} file(s) matching {source!r}...", verbose)
            for filepath in files:
                results = extractor.extract_from_file(filepath)
                result_set.add_many(results)
            progress(
                f"  Found {len(result_set)} unique email(s) from {len(files)} file(s)",
                verbose,
            )

        else:
            # File path
            progress(f"Reading {source}...", verbose)
            try:
                results = extractor.extract_from_file(source)
                result_set.add_many(results)
                progress(f"  Found {len(results)} email(s) from {source}", verbose)
            except FileNotFoundError:
                print(f"emx: error: file not found: {source}", file=sys.stderr)
            except PermissionError:
                print(f"emx: error: permission denied: {source}", file=sys.stderr)

    return result_set


def main(argv: Optional[List[str]] = None) -> int:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Auto-detect stdin if no sources given and stdin is piped
    sources = args.sources or []
    if not sources and detect_stdin():
        sources = ["-"]

    if not sources:
        parser.print_help(sys.stderr)
        return 2

    # Build extractor
    extractor = EmailExtractor(
        include_domains=args.include_domain,
        exclude_domains=args.exclude_domain,
        use_deobfuscate=not args.no_deobfuscate,
    )

    # Build crawler
    verbose = args.verbose and not args.quiet

    def on_page_done(url: str, pages_done: int, emails_found: int) -> None:
        progress(f"  [{pages_done} pages] {url} ({emails_found} emails so far)", verbose)

    crawler = WebCrawler(
        extractor=extractor,
        rate_limit=args.rate_limit,
        respect_robots=not args.ignore_robots,
        proxy=args.proxy,
        timeout=args.timeout,
        user_agent=args.user_agent,
        on_page_done=on_page_done if verbose else None,
    )

    # Process all sources
    try:
        result_set = _process_sources(sources, extractor, crawler, args)
    except KeyboardInterrupt:
        print("\nemx: interrupted", file=sys.stderr)
        return 130

    # Count mode
    if args.count:
        print(len(result_set))
        return 0 if len(result_set) > 0 else 1

    # Get results
    if args.with_source:
        results = result_set.results_all_sources()
    else:
        results = result_set.results()

    if not results:
        if not args.quiet:
            print("emx: no emails found", file=sys.stderr)
        return 1

    # Sort if requested
    if args.sort:
        results.sort(key=lambda r: r.email)

    # Format output
    output = format_results(results, fmt=args.output_format, with_source=args.with_source)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        if not args.quiet:
            progress(
                f"Wrote {len(results)} email(s) to {args.output}",
                verbose=True,
            )
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
