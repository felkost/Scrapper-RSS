"""Tests for tasks.exceptions module."""

from tasks.exceptions import UnhandledException, InvalidXMLError, InvalidRSSError


class TestExceptionHierarchy:
    """Verify that custom exceptions form the correct inheritance chain."""

    def test_invalid_xml_is_unhandled(self):
        assert issubclass(InvalidXMLError, UnhandledException)

    def test_invalid_rss_is_unhandled(self):
        assert issubclass(InvalidRSSError, UnhandledException)

    def test_unhandled_is_exception(self):
        assert issubclass(UnhandledException, Exception)

    def test_catch_invalid_xml_as_unhandled(self):
        try:
            raise InvalidXMLError("bad xml")
        except UnhandledException as e:
            assert str(e) == "bad xml"

    def test_catch_invalid_rss_as_unhandled(self):
        try:
            raise InvalidRSSError("no channel")
        except UnhandledException as e:
            assert str(e) == "no channel"
