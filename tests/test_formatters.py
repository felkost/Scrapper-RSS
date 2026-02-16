"""Tests for tasks.formatters module."""

import json

from tasks.formatters import (
    format_console,
    format_json,
    _format_category,
    CHANNEL_LABELS,
    ITEM_LABELS,
    CHANNEL_DISPLAY_ORDER,
    ITEM_DISPLAY_ORDER,
    ITEM_JSON_ORDER,
)


# ---------------------------------------------------------------------------
# _format_category
# ---------------------------------------------------------------------------

class TestFormatCategory:
    """Tests for the _format_category() helper."""

    def test_single(self):
        assert _format_category(["Tech"]) == "Tech"

    def test_multiple(self):
        assert _format_category(["A", "B", "C"]) == "A, B, C"


# ---------------------------------------------------------------------------
# format_console
# ---------------------------------------------------------------------------

class TestFormatConsole:
    """Tests for the format_console() function."""

    def test_channel_only(self):
        channel = {"title": "Feed", "link": "https://x.com", "description": "Desc"}
        lines = format_console(channel, [])
        assert lines == [
            "Feed: Feed",
            "Link: https://x.com",
            "Description: Desc",
        ]

    def test_channel_field_order(self):
        channel = {
            "description": "D",
            "title": "T",
            "language": "en",
            "link": "L",
        }
        lines = format_console(channel, [])
        assert lines == [
            "Feed: T",
            "Link: L",
            "Language: en",
            "Description: D",
        ]

    def test_channel_all_fields(self):
        channel = {
            "title": "T",
            "link": "L",
            "lastBuildDate": "LBD",
            "pubDate": "PD",
            "language": "en",
            "category": ["A", "B"],
            "managingEditor": "Ed",
            "description": "D",
        }
        lines = format_console(channel, [])
        assert lines == [
            "Feed: T",
            "Link: L",
            "Last Build Date: LBD",
            "Publish Date: PD",
            "Language: en",
            "Categories: A, B",
            "Editor: Ed",
            "Description: D",
        ]

    def test_single_item(self):
        channel = {"title": "T", "link": "L", "description": "D"}
        items = [{"title": "News", "link": "http://n", "description": "Body"}]
        lines = format_console(channel, items)
        assert lines == [
            "Feed: T",
            "Link: L",
            "Description: D",
            "",
            "Title: News",
            "Link: http://n",
            "",
            "Body",
        ]

    def test_item_field_order(self):
        channel = {"title": "T", "link": "L", "description": "D"}
        items = [{
            "title": "N",
            "author": "A",
            "pubDate": "P",
            "link": "LN",
            "category": ["C1"],
            "description": "Body",
        }]
        lines = format_console(channel, items)
        item_lines = lines[lines.index("") + 1:]
        assert item_lines == [
            "Title: N",
            "Author: A",
            "Published: P",
            "Link: LN",
            "Categories: C1",
            "",
            "Body",
        ]

    def test_multiple_items_separated(self):
        channel = {"title": "T", "link": "L", "description": "D"}
        items = [
            {"title": "A", "description": "Body A"},
            {"title": "B", "description": "Body B"},
        ]
        lines = format_console(channel, items)
        text = "\n".join(lines)
        assert "Body A\n\nTitle: B" in text

    def test_item_without_description(self):
        channel = {"title": "T", "link": "L", "description": "D"}
        items = [{"title": "News", "link": "http://n"}]
        lines = format_console(channel, items)
        assert lines == [
            "Feed: T",
            "Link: L",
            "Description: D",
            "",
            "Title: News",
            "Link: http://n",
        ]

    def test_missing_fields_skipped(self):
        channel = {"title": "T", "link": "L", "description": "D"}
        items = [{"title": "News"}]
        lines = format_console(channel, items)
        item_lines = lines[lines.index("") + 1:]
        assert item_lines == ["Title: News"]


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------

class TestFormatJson:
    """Tests for the format_json() function."""

    def _parse(self, channel_data, items):
        lines = format_json(channel_data, items)
        return json.loads("\n".join(lines))

    def test_channel_only_no_items_key(self):
        result = self._parse(
            {"title": "T", "link": "L", "description": "D"}, []
        )
        assert "items" not in result

    def test_channel_fields(self):
        result = self._parse(
            {"title": "T", "link": "L", "description": "D"}, []
        )
        assert result == {"title": "T", "link": "L", "description": "D"}

    def test_channel_field_order(self):
        data = {
            "description": "D",
            "title": "T",
            "language": "en",
            "link": "L",
        }
        lines = format_json(data, [])
        raw = "\n".join(lines)
        assert raw.index('"title"') < raw.index('"link"')
        assert raw.index('"link"') < raw.index('"language"')
        assert raw.index('"language"') < raw.index('"description"')

    def test_categories_as_list(self):
        result = self._parse(
            {"title": "T", "link": "L", "description": "D",
             "category": ["A", "B"]}, []
        )
        assert result["category"] == ["A", "B"]

    def test_items_present(self):
        result = self._parse(
            {"title": "T", "link": "L", "description": "D"},
            [{"title": "News", "description": "Body"}],
        )
        assert "items" in result
        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "News"

    def test_item_field_order(self):
        items = [{
            "description": "D",
            "title": "T",
            "author": "A",
            "pubDate": "P",
            "link": "L",
            "category": ["C"],
        }]
        lines = format_json({"title": "T", "link": "L", "description": "D"}, items)
        item_str = "\n".join(lines)
        assert item_str.index('"title"') < item_str.index('"author"')

    def test_indent_two_spaces(self):
        lines = format_json(
            {"title": "T", "link": "L", "description": "D"}, []
        )
        raw = "\n".join(lines)
        assert '  "title"' in raw

    def test_ensure_ascii_false(self):
        result = self._parse(
            {"title": "Новини", "link": "L", "description": "D"}, []
        )
        assert result["title"] == "Новини"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestFormatterConstants:
    """Verify that label mappings and order lists are consistent."""

    def test_channel_labels_cover_display_order(self):
        for field in CHANNEL_DISPLAY_ORDER:
            assert field in CHANNEL_LABELS

    def test_item_labels_cover_display_order(self):
        for field in ITEM_DISPLAY_ORDER:
            assert field in ITEM_LABELS

    def test_item_json_order_includes_description(self):
        assert "description" in ITEM_JSON_ORDER
        assert "description" not in ITEM_DISPLAY_ORDER
