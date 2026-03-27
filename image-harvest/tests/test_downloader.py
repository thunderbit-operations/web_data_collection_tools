"""Tests for the image downloader."""

import os

import pytest
import responses

from image_extractor.downloader import ImageDownloader
from image_extractor.utils import ImageInfo


def _make_image(url="https://example.com/photo.jpg", filename="photo.jpg", ext="jpg"):
    return ImageInfo(url=url, alt="", source_page="https://example.com", filename=filename, extension=ext)


class TestDownloader:
    @responses.activate
    def test_download_single(self, tmp_path):
        responses.add(responses.GET, "https://example.com/photo.jpg",
                      body=b"\x89PNG fake image data", status=200,
                      headers={"content-length": "20"})

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1)
        stats = dl.download([_make_image()])
        assert stats["downloaded"] == 1
        assert os.path.exists(os.path.join(str(tmp_path), "photo.jpg"))

    @responses.activate
    def test_skip_existing(self, tmp_path):
        # Create existing file
        filepath = tmp_path / "photo.jpg"
        filepath.write_bytes(b"existing")

        responses.add(responses.GET, "https://example.com/photo.jpg",
                      body=b"new data", status=200)

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1, overwrite=False)
        stats = dl.download([_make_image()])
        assert stats["skipped"] == 1
        assert stats["downloaded"] == 0

    @responses.activate
    def test_overwrite(self, tmp_path):
        filepath = tmp_path / "photo.jpg"
        filepath.write_bytes(b"old")

        responses.add(responses.GET, "https://example.com/photo.jpg",
                      body=b"new data", status=200,
                      headers={"content-length": "8"})

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1, overwrite=True)
        stats = dl.download([_make_image()])
        assert stats["downloaded"] == 1
        assert filepath.read_bytes() == b"new data"

    @responses.activate
    def test_dedupe_by_hash(self, tmp_path):
        # Two different URLs, same content
        responses.add(responses.GET, "https://example.com/a.jpg",
                      body=b"identical content", status=200)
        responses.add(responses.GET, "https://example.com/b.jpg",
                      body=b"identical content", status=200)

        images = [
            _make_image("https://example.com/a.jpg", "a.jpg"),
            _make_image("https://example.com/b.jpg", "b.jpg"),
        ]
        dl = ImageDownloader(output_dir=str(tmp_path), workers=1, dedupe=True)
        stats = dl.download(images)
        assert stats["downloaded"] == 1
        assert stats["skipped"] == 1

    @responses.activate
    def test_max_size(self, tmp_path):
        responses.add(responses.GET, "https://example.com/big.jpg",
                      body=b"x" * 2000, status=200,
                      headers={"content-length": "2000"})

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1,
                             max_size_mb=0.001)  # ~1KB limit
        stats = dl.download([_make_image("https://example.com/big.jpg", "big.jpg")])
        assert stats["skipped"] == 1

    @responses.activate
    def test_rename_pattern(self, tmp_path):
        responses.add(responses.GET, "https://example.com/photo.jpg",
                      body=b"data", status=200)

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1,
                             rename_pattern="{n:04d}.{ext}")
        stats = dl.download([_make_image()])
        assert stats["downloaded"] == 1
        assert os.path.exists(os.path.join(str(tmp_path), "0001.jpg"))

    @responses.activate
    def test_handles_failure(self, tmp_path):
        responses.add(responses.GET, "https://example.com/broken.jpg", status=404)

        dl = ImageDownloader(output_dir=str(tmp_path), workers=1)
        stats = dl.download([_make_image("https://example.com/broken.jpg", "broken.jpg")])
        assert stats["failed"] == 1

    @responses.activate
    def test_parallel_download(self, tmp_path):
        for i in range(5):
            responses.add(responses.GET, f"https://example.com/img{i}.jpg",
                          body=f"data{i}".encode(), status=200)

        images = [_make_image(f"https://example.com/img{i}.jpg", f"img{i}.jpg") for i in range(5)]
        dl = ImageDownloader(output_dir=str(tmp_path), workers=4)
        stats = dl.download(images)
        assert stats["downloaded"] == 5
