"""Tests for tasks.rss_reader module (orchestrator + CLI)."""

import json
from unittest.mock import patch, MagicMock

import pytest

from tasks.rss_reader import rss_parser, main
from tasks.exceptions import (
    UnhandledException,
    InvalidXMLError,
    InvalidRSSError,
)


# ---------------------------------------------------------------------------
# Helper: build RSS XML strings
# ---------------------------------------------------------------------------

def _rss(channel_body):
    return f"<rss version='2.0'><channel>{channel_body}</channel></rss>"


MINIMAL_CHANNEL = _rss(
    "<title>T</title><link>L</link><description>D</description>"
)


# ---------------------------------------------------------------------------
# rss_parser — console output
# ---------------------------------------------------------------------------

class TestRssParserConsole:
    """Tests for rss_parser() with console (default) output."""

    def test_minimal_channel(self):
        assert rss_parser(MINIMAL_CHANNEL) == [
            "Feed: T", "Link: L", "Description: D",
        ]

    def test_channel_with_items(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>News</title><description>Body</description></item>"
        )
        lines = rss_parser(xml)
        assert "Feed: T" in lines
        assert "Title: News" in lines
        assert "Body" in lines

    def test_limit_applied(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>A</title></item>"
            "<item><title>B</title></item>"
            "<item><title>C</title></item>"
        )
        lines = rss_parser(xml, limit=1)
        assert "Title: A" in lines
        assert "Title: B" not in lines

    def test_limit_none_returns_all(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>A</title></item>"
            "<item><title>B</title></item>"
        )
        lines = rss_parser(xml, limit=None)
        assert "Title: A" in lines
        assert "Title: B" in lines

    def test_limit_exceeds_feed_returns_all(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>A</title></item>"
        )
        lines = rss_parser(xml, limit=999)
        assert "Title: A" in lines

    def test_html_entities_decoded(self):
        xml = _rss(
            "<title>News &amp; More</title>"
            "<link>L</link>"
            "<description>It&#39;s good</description>"
        )
        lines = rss_parser(xml)
        assert "Feed: News & More" in lines
        assert "Description: It's good" in lines


# ---------------------------------------------------------------------------
# rss_parser — JSON output
# ---------------------------------------------------------------------------

class TestRssParserJson:
    """Tests for rss_parser() with json=True."""

    def _parse_json(self, xml, **kwargs):
        lines = rss_parser(xml, json=True, **kwargs)
        return json.loads("\n".join(lines))

    def test_minimal_channel(self):
        result = self._parse_json(MINIMAL_CHANNEL)
        assert result == {"title": "T", "link": "L", "description": "D"}

    def test_no_items_key_when_empty(self):
        result = self._parse_json(MINIMAL_CHANNEL)
        assert "items" not in result

    def test_items_present(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>N</title><description>B</description></item>"
        )
        result = self._parse_json(xml)
        assert len(result["items"]) == 1

    def test_categories_as_list(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<category>A</category><category>B</category>"
        )
        result = self._parse_json(xml)
        assert result["category"] == ["A", "B"]

    def test_limit_affects_json(self):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>A</title></item>"
            "<item><title>B</title></item>"
        )
        result = self._parse_json(xml, limit=1)
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "A"

    def test_indent_two_spaces(self):
        lines = rss_parser(MINIMAL_CHANNEL, json=True)
        raw = "\n".join(lines)
        assert '  "title"' in raw


# ---------------------------------------------------------------------------
# rss_parser — error handling
# ---------------------------------------------------------------------------

class TestRssParserErrors:
    """Tests for rss_parser() error handling."""

    def test_invalid_xml_raises(self):
        with pytest.raises(InvalidXMLError):
            rss_parser("not xml at all")

    def test_no_channel_raises(self):
        with pytest.raises(InvalidRSSError):
            rss_parser("<rss></rss>")

    def test_invalid_xml_is_unhandled(self):
        with pytest.raises(UnhandledException):
            rss_parser("<broken>")


# ---------------------------------------------------------------------------
# Backwards-compatible imports
# ---------------------------------------------------------------------------

class TestImports:
    """Verify that key names remain importable from tasks.rss_reader."""

    def test_unhandled_exception_importable(self):
        from tasks.rss_reader import UnhandledException  # noqa: F811
        assert issubclass(UnhandledException, Exception)

    def test_rss_parser_importable(self):
        from tasks.rss_reader import rss_parser  # noqa: F811
        assert callable(rss_parser)

    def test_main_importable(self):
        from tasks.rss_reader import main  # noqa: F811
        assert callable(main)


# ---------------------------------------------------------------------------
# main() — CLI integration
# ---------------------------------------------------------------------------

class TestMain:
    """Tests for main() CLI entry point."""

    def test_console_output(self, capsys):
        mock_response = MagicMock()
        mock_response.text = MINIMAL_CHANNEL
        mock_response.apparent_encoding = "utf-8"

        with patch("tasks.rss_reader.requests.get", return_value=mock_response):
            result = main(["https://example.com/rss"])

        assert result == 0
        captured = capsys.readouterr()
        assert "Feed: T" in captured.out

    def test_json_output(self, capsys):
        mock_response = MagicMock()
        mock_response.text = MINIMAL_CHANNEL
        mock_response.apparent_encoding = "utf-8"

        with patch("tasks.rss_reader.requests.get", return_value=mock_response):
            result = main(["https://example.com/rss", "--json"])

        assert result == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["title"] == "T"

    def test_limit_passed_through(self, capsys):
        xml = _rss(
            "<title>T</title><link>L</link><description>D</description>"
            "<item><title>A</title></item>"
            "<item><title>B</title></item>"
        )
        mock_response = MagicMock()
        mock_response.text = xml
        mock_response.apparent_encoding = "utf-8"

        with patch("tasks.rss_reader.requests.get", return_value=mock_response):
            main(["https://example.com/rss", "--limit", "1"])

        captured = capsys.readouterr()
        assert "Title: A" in captured.out
        assert "Title: B" not in captured.out
