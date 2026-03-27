"""Parallel image downloader with deduplication and resume support."""

import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Optional, Set

import requests

from image_extractor.utils import (
    ImageInfo,
    content_hash,
    progress,
    sanitize_filename,
    url_to_filename,
)


class ImageDownloader:
    """Download images in parallel with deduplication and resume support.

    Usage::

        downloader = ImageDownloader(output_dir="./images", workers=8)
        stats = downloader.download(image_list)
        print(f"Downloaded {stats['downloaded']}, skipped {stats['skipped']}")
    """

    def __init__(
        self,
        output_dir: str = "./images",
        workers: int = 4,
        timeout: int = 30,
        user_agent: str = "ImageHarvest/1.0",
        overwrite: bool = False,
        dedupe: bool = True,
        max_size_mb: float = 0,
        rename_pattern: Optional[str] = None,
        on_download: Optional[Callable[[str, str, bool], None]] = None,
    ):
        """
        Args:
            output_dir: Directory to save images.
            workers: Number of parallel download threads.
            timeout: Download timeout per image in seconds.
            user_agent: User-Agent header.
            overwrite: Overwrite existing files.
            dedupe: Skip duplicate images (by content hash).
            max_size_mb: Skip images larger than this (0 = no limit).
            rename_pattern: Rename pattern with {n} for index, {ext} for extension.
            on_download: Callback(url, filepath, success) after each download.
        """
        self.output_dir = output_dir
        self.workers = workers
        self.timeout = timeout
        self.user_agent = user_agent
        self.overwrite = overwrite
        self.dedupe = dedupe
        self.max_size_bytes = int(max_size_mb * 1024 * 1024) if max_size_mb > 0 else 0
        self.rename_pattern = rename_pattern
        self.on_download = on_download

    def _get_filepath(self, image: ImageInfo, index: int) -> str:
        """Determine the output file path."""
        if self.rename_pattern:
            filename = self.rename_pattern.format(
                n=index, ext=image.extension, name=image.filename.rsplit(".", 1)[0]
            )
            if "." not in filename:
                filename = f"{filename}.{image.extension}"
        else:
            filename = sanitize_filename(image.filename)
        return os.path.join(self.output_dir, filename)

    def _download_one(
        self,
        image: ImageInfo,
        index: int,
        seen_hashes: Set[str],
    ) -> dict:
        """Download a single image. Returns stats dict."""
        filepath = self._get_filepath(image, index)

        # Resume: skip existing files
        if not self.overwrite and os.path.exists(filepath):
            return {"status": "skipped", "reason": "exists", "url": image.url, "path": filepath}

        try:
            headers = {"User-Agent": self.user_agent}
            resp = requests.get(image.url, headers=headers, timeout=self.timeout, stream=True)
            resp.raise_for_status()

            # Check content-length before downloading
            content_length = int(resp.headers.get("content-length", 0))
            if self.max_size_bytes > 0 and content_length > self.max_size_bytes:
                return {"status": "skipped", "reason": "too_large", "url": image.url, "path": filepath}

            data = resp.content

            # Size check on actual data
            if self.max_size_bytes > 0 and len(data) > self.max_size_bytes:
                return {"status": "skipped", "reason": "too_large", "url": image.url, "path": filepath}

            # Deduplication by content hash
            if self.dedupe:
                h = content_hash(data)
                if h in seen_hashes:
                    return {"status": "skipped", "reason": "duplicate", "url": image.url, "path": filepath}
                seen_hashes.add(h)

            # Write file
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            with open(filepath, "wb") as f:
                f.write(data)

            return {
                "status": "downloaded",
                "url": image.url,
                "path": filepath,
                "size": len(data),
            }

        except Exception as e:
            return {"status": "failed", "url": image.url, "path": filepath, "error": str(e)}

    def download(self, images: List[ImageInfo]) -> dict:
        """Download all images in parallel.

        Args:
            images: List of ImageInfo objects to download.

        Returns:
            Stats dict with counts: downloaded, skipped, failed, total_bytes.
        """
        os.makedirs(self.output_dir, exist_ok=True)

        seen_hashes: Set[str] = set()
        stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total_bytes": 0}
        results: List[dict] = []

        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futures = {
                pool.submit(self._download_one, img, i, seen_hashes): img
                for i, img in enumerate(images, 1)
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result["status"] == "downloaded":
                    stats["downloaded"] += 1
                    stats["total_bytes"] += result.get("size", 0)
                elif result["status"] == "skipped":
                    stats["skipped"] += 1
                elif result["status"] == "failed":
                    stats["failed"] += 1

                if self.on_download:
                    self.on_download(
                        result["url"],
                        result.get("path", ""),
                        result["status"] == "downloaded",
                    )

        stats["results"] = results
        return stats
