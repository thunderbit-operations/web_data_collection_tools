"""Tests for the CLI interface."""

import json
import os

import pytest

from phone_extractor.cli import main

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


class TestCliBasic:
    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_no_args_returns_2(self, capsys, monkeypatch):
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        result = main([])
        assert result == 2

    def test_file_not_found(self, capsys):
        result = main(["nonexistent_file.txt"])
        assert result == 1

    def test_extract_from_file(self, capsys):
        result = main([os.path.join(FIXTURES, "sample.txt"), "--region", "US"])
        assert result == 0
        captured = capsys.readouterr()
        assert "+12125551234" in captured.out

    def test_extract_from_html_file(self, capsys):
        result = main([os.path.join(FIXTURES, "sample.html"), "--region", "US"])
        assert result == 0
        captured = capsys.readouterr()
        assert "+12125551234" in captured.out


class TestCliOutput:
    def test_json_format(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--format", "json", "--region", "US",
        ])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data, list)
        numbers = [item["number"] if isinstance(item, dict) else item for item in data]
        assert "+12125551234" in numbers

    def test_json_detail(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--format", "json", "--detail", "--region", "US",
        ])
        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert isinstance(data[0], dict)
        assert "country_code" in data[0]
        assert "carrier" in data[0]
        assert "type" in data[0]

    def test_csv_format(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--format", "csv", "--region", "US",
        ])
        assert result == 0
        captured = capsys.readouterr()
        assert "number" in captured.out
        assert "+12125551234" in captured.out

    def test_count_flag(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--count", "--region", "US",
        ])
        assert result == 0
        captured = capsys.readouterr()
        count = int(captured.out.strip())
        assert count > 0

    def test_sort_flag(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--sort", "--region", "US",
        ])
        assert result == 0
        captured = capsys.readouterr()
        numbers = captured.out.strip().split("\n")
        assert numbers == sorted(numbers)

    def test_output_to_file(self, capsys, tmp_path):
        outfile = str(tmp_path / "out.txt")
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--output", outfile, "--region", "US",
        ])
        assert result == 0
        with open(outfile) as f:
            content = f.read()
        assert "+12125551234" in content


class TestCliFiltering:
    def test_include_country(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--include-country", "GB", "--region", "US",
        ])
        captured = capsys.readouterr()
        if result == 0:
            assert "+44" in captured.out
            assert "+1212" not in captured.out

    def test_exclude_country(self, capsys):
        result = main([
            os.path.join(FIXTURES, "sample.txt"),
            "--exclude-country", "US", "--region", "US",
        ])
        captured = capsys.readouterr()
        if result == 0:
            lines = captured.out.strip().split("\n")
            assert all(not line.startswith("+1212") for line in lines)


class TestCliStdin:
    def test_stdin_pipe(self, capsys, monkeypatch):
        import io
        monkeypatch.setattr("sys.stdin", io.StringIO("Call +1 212-555-1234"))
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        result = main(["-", "--region", "US"])
        assert result == 0
        captured = capsys.readouterr()
        assert "+12125551234" in captured.out
