"""Tests for tasks.parser module."""

import pytest
from xml.etree.ElementTree import fromstring

from tasks.parser import (
    get_text,
    parse_categories,
    parse_channel,
    parse_items,
    CHANNEL_FIELDS,
    ITEM_FIELDS,
)


# ---------------------------------------------------------------------------
# get_text
# ---------------------------------------------------------------------------

class TestGetText:
    """Tests for the get_text() text extraction function."""

    def test_none_element(self):
        assert get_text(None) is None

    def test_simple_text(self):
        elem = fromstring("<tag>hello</tag>")
        assert get_text(elem) == "hello"

    def test_strips_whitespace(self):
        elem = fromstring("<tag>  spaced  </tag>")
        assert get_text(elem) == "spaced"

    def test_empty_element(self):
        elem = fromstring("<tag></tag>")
        assert get_text(elem) is None

    def test_whitespace_only(self):
        elem = fromstring("<tag>   </tag>")
        assert get_text(elem) is None

    def test_html_entity_amp(self):
        elem = fromstring("<tag>News &amp; More</tag>")
        assert get_text(elem) == "News & More"

    def test_html_entity_numeric(self):
        elem = fromstring("<tag>it&#39;s</tag>")
        assert get_text(elem) == "it's"

    def test_html_entity_hex(self):
        elem = fromstring("<tag>quote&#x2019;s</tag>")
        assert get_text(elem) == "quote\u2019s"

    def test_nested_elements(self):
        elem = fromstring("<tag>hello <b>world</b></tag>")
        assert get_text(elem) == "hello world"


# ---------------------------------------------------------------------------
# parse_categories
# ---------------------------------------------------------------------------

class TestParseCategories:
    """Tests for the parse_categories() function."""

    def test_no_categories(self):
        parent = fromstring("<channel><title>T</title></channel>")
        assert parse_categories(parent) is None

    def test_single_category(self):
        parent = fromstring(
            "<channel><category>Tech</category></channel>"
        )
        assert parse_categories(parent) == ["Tech"]

    def test_multiple_categories(self):
        parent = fromstring(
            "<channel>"
            "<category>News</category>"
            "<category>Sports</category>"
            "<category>Tech</category>"
            "</channel>"
        )
        assert parse_categories(parent) == ["News", "Sports", "Tech"]

    def test_empty_category_skipped(self):
        parent = fromstring(
            "<channel>"
            "<category>News</category>"
            "<category></category>"
            "<category>Tech</category>"
            "</channel>"
        )
        assert parse_categories(parent) == ["News", "Tech"]

    def test_all_empty_categories(self):
        parent = fromstring(
            "<channel>"
            "<category></category>"
            "<category>   </category>"
            "</channel>"
        )
        assert parse_categories(parent) is None


# ---------------------------------------------------------------------------
# parse_channel
# ---------------------------------------------------------------------------

class TestParseChannel:
    """Tests for the parse_channel() function."""

    def test_required_fields_only(self):
        channel = fromstring(
            "<channel>"
            "<title>My Feed</title>"
            "<link>https://example.com</link>"
            "<description>A feed</description>"
            "</channel>"
        )
        data = parse_channel(channel)
        assert data == {
            "title": "My Feed",
            "link": "https://example.com",
            "description": "A feed",
        }

    def test_all_fields(self):
        channel = fromstring(
            "<channel>"
            "<title>Feed</title>"
            "<link>https://x.com</link>"
            "<lastBuildDate>Mon, 01 Jan 2024</lastBuildDate>"
            "<pubDate>Sun, 31 Dec 2023</pubDate>"
            "<language>en-us</language>"
            "<managingEditor>editor@x.com</managingEditor>"
            "<description>Desc</description>"
            "<category>News</category>"
            "<category>Tech</category>"
            "</channel>"
        )
        data = parse_channel(channel)
        assert data["title"] == "Feed"
        assert data["link"] == "https://x.com"
        assert data["lastBuildDate"] == "Mon, 01 Jan 2024"
        assert data["pubDate"] == "Sun, 31 Dec 2023"
        assert data["language"] == "en-us"
        assert data["managingEditor"] == "editor@x.com"
        assert data["description"] == "Desc"
        assert data["category"] == ["News", "Tech"]

    def test_missing_optional_fields(self):
        channel = fromstring(
            "<channel>"
            "<title>Feed</title>"
            "<link>https://x.com</link>"
            "<description>Desc</description>"
            "</channel>"
        )
        data = parse_channel(channel)
        assert "lastBuildDate" not in data
        assert "pubDate" not in data
        assert "language" not in data
        assert "managingEditor" not in data
        assert "category" not in data

    def test_html_entities_decoded(self):
        channel = fromstring(
            "<channel>"
            "<title>News &amp; Updates</title>"
            "<link>https://x.com</link>"
            "<description>It&#39;s great</description>"
            "</channel>"
        )
        data = parse_channel(channel)
        assert data["title"] == "News & Updates"
        assert data["description"] == "It's great"


# ---------------------------------------------------------------------------
# parse_items
# ---------------------------------------------------------------------------

class TestParseItems:
    """Tests for the parse_items() function."""

    def _channel_with_items(self, *items_xml):
        xml = (
            "<channel>"
            "<title>T</title><link>L</link><description>D</description>"
            + "".join(items_xml)
            + "</channel>"
        )
        return fromstring(xml)

    def test_no_items(self):
        channel = self._channel_with_items()
        assert parse_items(channel, None) == []

    def test_single_item(self):
        channel = self._channel_with_items(
            "<item><title>News 1</title>"
            "<description>Body 1</description></item>"
        )
        items = parse_items(channel, None)
        assert len(items) == 1
        assert items[0]["title"] == "News 1"
        assert items[0]["description"] == "Body 1"

    def test_multiple_items(self):
        channel = self._channel_with_items(
            "<item><title>A</title></item>",
            "<item><title>B</title></item>",
            "<item><title>C</title></item>",
        )
        items = parse_items(channel, None)
        assert len(items) == 3
        assert [i["title"] for i in items] == ["A", "B", "C"]

    def test_limit_fewer_than_available(self):
        channel = self._channel_with_items(
            "<item><title>A</title></item>",
            "<item><title>B</title></item>",
            "<item><title>C</title></item>",
        )
        items = parse_items(channel, 2)
        assert len(items) == 2
        assert [i["title"] for i in items] == ["A", "B"]

    def test_limit_more_than_available(self):
        channel = self._channel_with_items(
            "<item><title>A</title></item>",
        )
        items = parse_items(channel, 100)
        assert len(items) == 1

    def test_limit_zero(self):
        channel = self._channel_with_items(
            "<item><title>A</title></item>",
        )
        assert parse_items(channel, 0) == []

    def test_item_all_fields(self):
        channel = self._channel_with_items(
            "<item>"
            "<title>Title</title>"
            "<author>Author</author>"
            "<pubDate>Mon, 01 Jan 2024</pubDate>"
            "<link>https://x.com/1</link>"
            "<category>Tech</category>"
            "<category>AI</category>"
            "<description>Body text</description>"
            "</item>"
        )
        item = parse_items(channel, None)[0]
        assert item["title"] == "Title"
        assert item["author"] == "Author"
        assert item["pubDate"] == "Mon, 01 Jan 2024"
        assert item["link"] == "https://x.com/1"
        assert item["category"] == ["Tech", "AI"]
        assert item["description"] == "Body text"

    def test_item_missing_optional_fields(self):
        channel = self._channel_with_items(
            "<item><title>Only Title</title></item>"
        )
        item = parse_items(channel, None)[0]
        assert "author" not in item
        assert "pubDate" not in item
        assert "link" not in item
        assert "category" not in item
        assert "description" not in item


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    """Verify that field lists contain expected tags."""

    def test_channel_fields_order(self):
        assert CHANNEL_FIELDS == [
            'title', 'link', 'lastBuildDate', 'pubDate',
            'language', 'managingEditor', 'description',
        ]

    def test_item_fields_order(self):
        assert ITEM_FIELDS == [
            'title', 'author', 'pubDate', 'link', 'description',
        ]
