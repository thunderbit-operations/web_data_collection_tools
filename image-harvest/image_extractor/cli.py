"""Command-line interface for image-harvest."""

import argparse
import json
import sys
from typing import List, Optional

from image_extractor import __version__
from image_extractor.crawler import ImageCrawler
from image_extractor.downloader import ImageDownloader
from image_extractor.extractor import ImageExtractor
from image_extractor.utils import ImageInfo, is_url, progress


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="imgx",
        description="Download images from web pages in batch.",
        epilog="Examples:\n"
        "  imgx https://example.com\n"
        "  imgx https://example.com -o ./photos --min-width 200\n"
        "  imgx https://example.com --type jpg,png --workers 8\n"
        "  imgx https://example.com --depth 2 --list-only\n"
        '  imgx https://example.com --rename "{n:04d}.{ext}"\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "urls",
        nargs="+",
        metavar="URL",
        help="web page URLs to extract images from",
    )

    # Output
    out = parser.add_argument_group("output")
    out.add_argument(
        "-o", "--output",
        default="./images",
        metavar="DIR",
        help="output directory (default: ./images)",
    )
    out.add_argument(
        "--list-only",
        action="store_true",
        help="only list image URLs, don't download",
    )
    out.add_argument(
        "--list-format",
        choices=["plain", "json", "jsonl"],
        default="plain",
        help="format for --list-only output (default: plain)",
    )

    # Filtering
    filt = parser.add_argument_group("filtering")
    filt.add_argument(
        "--min-width",
        type=int,
        default=0,
        help="minimum image width in pixels (from HTML attributes)",
    )
    filt.add_argument(
        "--min-height",
        type=int,
        default=0,
        help="minimum image height in pixels (from HTML attributes)",
    )
    filt.add_argument(
        "--type",
        metavar="EXT",
        help="only download these types, comma-separated (e.g., jpg,png,webp)",
    )
    filt.add_argument(
        "--exclude-type",
        metavar="EXT",
        help="exclude these types, comma-separated",
    )
    filt.add_argument(
        "--include-svg",
        action="store_true",
        help="include SVG images (excluded by default)",
    )
    filt.add_argument(
        "--max-size",
        type=float,
        default=0,
        metavar="MB",
        help="skip images larger than this (MB, 0 = no limit)",
    )

    # Download
    dl = parser.add_argument_group("download")
    dl.add_argument(
        "--workers", "-w",
        type=int,
        default=4,
        help="parallel download threads (default: 4)",
    )
    dl.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite existing files",
    )
    dl.add_argument(
        "--no-dedupe",
        action="store_true",
        help="disable content-hash deduplication",
    )
    dl.add_argument(
        "--rename",
        metavar="PATTERN",
        help='rename files: "{n:04d}.{ext}" or "{name}_{n}.{ext}"',
    )
    dl.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="download timeout per image in seconds (default: 30)",
    )

    # Crawling
    crawl = parser.add_argument_group("crawling")
    crawl.add_argument(
        "--depth",
        type=int,
        default=0,
        help="recursion depth (0 = single page, default: 0)",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=50,
        help="max pages to crawl (default: 50)",
    )
    crawl.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="seconds between page requests (default: 1.0)",
    )
    crawl.add_argument(
        "--ignore-robots",
        action="store_true",
        help="ignore robots.txt",
    )
    crawl.add_argument(
        "--proxy",
        help="HTTP/HTTPS proxy URL",
    )
    crawl.add_argument(
        "--user-agent",
        default="ImageHarvest/1.0",
        help="custom User-Agent",
    )

    # Meta
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="show progress on stderr")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="suppress all non-output messages")
    parser.add_argument("--version", action="version",
                        version=f"%(prog)s {__version__}")

    return parser


def _list_images(images: List[ImageInfo], fmt: str) -> str:
    """Format image list for --list-only output."""
    if fmt == "json":
        data = [{"url": img.url, "filename": img.filename, "alt": img.alt, "source": img.source_page}
                for img in images]
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif fmt == "jsonl":
        lines = []
        for img in images:
            lines.append(json.dumps({"url": img.url, "filename": img.filename}, ensure_ascii=False))
        return "\n".join(lines)
    else:
        return "\n".join(img.url for img in images)


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    verbose = args.verbose and not args.quiet

    # Parse type filters
    include_types = args.type.split(",") if args.type else None
    exclude_types = args.exclude_type.split(",") if args.exclude_type else None

    # Build extractor
    extractor = ImageExtractor(
        min_width=args.min_width,
        min_height=args.min_height,
        include_types=include_types,
        exclude_types=exclude_types,
        include_svg=args.include_svg,
        timeout=args.timeout,
        user_agent=args.user_agent,
    )

    # Build crawler
    def on_page_done(url: str, pages: int, imgs: int) -> None:
        progress(f"  [{pages} pages] {url} ({imgs} images found)", verbose)

    crawler = ImageCrawler(
        extractor=extractor,
        rate_limit=args.rate_limit,
        respect_robots=not args.ignore_robots,
        proxy=args.proxy,
        timeout=min(args.timeout, 10),
        user_agent=args.user_agent,
        on_page_done=on_page_done if verbose else None,
    )

    # Discover images
    all_images: List[ImageInfo] = []
    try:
        for url in args.urls:
            if args.depth > 0:
                progress(f"Crawling {url} (depth={args.depth})...", verbose)
                images = crawler.crawl(url, max_depth=args.depth, max_pages=args.max_pages)
            else:
                progress(f"Fetching {url}...", verbose)
                images = extractor.from_url(url)
            all_images.extend(images)
            progress(f"  Found {len(images)} image(s)", verbose)
    except KeyboardInterrupt:
        print("\nimgx: interrupted", file=sys.stderr)
        return 130

    if not all_images:
        if not args.quiet:
            print("imgx: no images found", file=sys.stderr)
        return 1

    # Deduplicate by URL across all sources
    seen_urls = set()
    unique_images = []
    for img in all_images:
        if img.url not in seen_urls:
            seen_urls.add(img.url)
            unique_images.append(img)
    all_images = unique_images

    progress(f"Found {len(all_images)} unique image(s) total", verbose)

    # List-only mode
    if args.list_only:
        print(_list_images(all_images, args.list_format))
        return 0

    # Download
    def on_download(url: str, path: str, success: bool) -> None:
        if success:
            progress(f"  Downloaded: {path}", verbose)
        else:
            progress(f"  Failed: {url}", verbose)

    downloader = ImageDownloader(
        output_dir=args.output,
        workers=args.workers,
        timeout=args.timeout,
        user_agent=args.user_agent,
        overwrite=args.overwrite,
        dedupe=not args.no_dedupe,
        max_size_mb=args.max_size,
        rename_pattern=args.rename,
        on_download=on_download if verbose else None,
    )

    try:
        stats = downloader.download(all_images)
    except KeyboardInterrupt:
        print("\nimgx: interrupted", file=sys.stderr)
        return 130

    if not args.quiet:
        msg = (
            f"Done: {stats['downloaded']} downloaded, "
            f"{stats['skipped']} skipped, "
            f"{stats['failed']} failed"
        )
        if stats["total_bytes"] > 1024 * 1024:
            msg += f" ({stats['total_bytes'] / 1024 / 1024:.1f} MB)"
        elif stats["total_bytes"] > 1024:
            msg += f" ({stats['total_bytes'] / 1024:.0f} KB)"
        progress(msg, verbose=True)

    return 0 if stats["downloaded"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
