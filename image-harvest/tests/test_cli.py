"""Tests for the CLI interface."""

import json
import os

import pytest
import responses

from image_extractor.cli import main

GALLERY_HTML = open(os.path.join(os.path.dirname(__file__), "fixtures", "gallery.html")).read()


class TestCliListOnly:
    @responses.activate
    def test_list_plain(self, capsys):
        responses.add(responses.GET, "https://example.com/gallery",
                      body=GALLERY_HTML, status=200)
        result = main(["https://example.com/gallery", "--list-only"])
        assert result == 0
        captured = capsys.readouterr()
        assert "sunset.jpg" in captured.out

    @responses.activate
    def test_list_json(self, capsys):
        responses.add(responses.GET, "https://example.com/gallery",
                      body=GALLERY_HTML, status=200)
        result = main(["https://example.com/gallery", "--list-only", "--list-format", "json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        assert any("sunset.jpg" in item["url"] for item in data)

    @responses.activate
    def test_list_jsonl(self, capsys):
        responses.add(responses.GET, "https://example.com/gallery",
                      body=GALLERY_HTML, status=200)
        result = main(["https://example.com/gallery", "--list-only", "--list-format", "jsonl"])
        assert result == 0
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        for line in lines:
            obj = json.loads(line)
            assert "url" in obj


class TestCliFiltering:
    @responses.activate
    def test_type_filter(self, capsys):
        responses.add(responses.GET, "https://example.com/gallery",
                      body=GALLERY_HTML, status=200)
        result = main(["https://example.com/gallery", "--list-only", "--type", "jpg"])
        assert result == 0
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert all(line.endswith(".jpg") for line in lines if line)

    @responses.activate
    def test_include_svg(self, capsys):
        responses.add(responses.GET, "https://example.com/gallery",
                      body=GALLERY_HTML, status=200)
        result = main(["https://example.com/gallery", "--list-only", "--include-svg"])
        assert result == 0
        captured = capsys.readouterr()
        assert ".svg" in captured.out


class TestCliMeta:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_no_args(self, capsys):
        with pytest.raises(SystemExit):
            main([])
