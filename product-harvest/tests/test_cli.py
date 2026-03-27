"""Tests for the CLI interface."""

import json
import os

import pytest
import responses

from product_extractor.cli import main

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

with open(os.path.join(FIXTURES, "jsonld_product.html")) as f:
    JSONLD_HTML = f.read()


class TestCliBasic:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_no_args(self, capsys, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        result = main([])
        assert result == 2

    @responses.activate
    def test_extract_from_url(self, capsys):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        result = main(["https://shop.example.com/headphones"])
        assert result == 0
        captured = capsys.readouterr()
        assert "ProMax" in captured.out

    @responses.activate
    def test_no_product_found(self, capsys):
        responses.add(responses.GET, "https://example.com/about",
                      body="<html><body>No products</body></html>", status=200)
        result = main(["https://example.com/about"])
        assert result == 1


class TestCliOutput:
    @responses.activate
    def test_json_format(self, capsys):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        result = main(["https://shop.example.com/headphones", "--format", "json"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data[0]["name"] == "ProMax Wireless Headphones"

    @responses.activate
    def test_csv_format(self, capsys):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        result = main(["https://shop.example.com/headphones", "--format", "csv"])
        assert result == 0
        captured = capsys.readouterr()
        assert "name" in captured.out
        assert "ProMax" in captured.out

    @responses.activate
    def test_detail_flag(self, capsys):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        result = main(["https://shop.example.com/headphones", "--format", "json", "--detail"])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "sku" in data[0]
        assert "description" in data[0]

    @responses.activate
    def test_output_to_file(self, capsys, tmp_path):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        outfile = str(tmp_path / "out.json")
        result = main(["https://shop.example.com/headphones", "--format", "json", "-o", outfile])
        assert result == 0
        with open(outfile) as f:
            data = json.loads(f.read())
        assert data[0]["name"] == "ProMax Wireless Headphones"


class TestCliFileInput:
    @responses.activate
    def test_urls_from_file(self, capsys, tmp_path):
        responses.add(responses.GET, "https://shop.example.com/headphones",
                      body=JSONLD_HTML, status=200)
        url_file = tmp_path / "urls.txt"
        url_file.write_text("https://shop.example.com/headphones\n")
        result = main(["--file", str(url_file)])
        assert result == 0
        captured = capsys.readouterr()
        assert "ProMax" in captured.out
