# You shouldn't change  name of function or their arguments
# but you can change content of the initial functions.
from argparse import ArgumentParser
from typing import List, Optional, Sequence
from xml.etree.ElementTree import fromstring
import requests

from tasks.exceptions import UnhandledException, InvalidXMLError, InvalidRSSError
from tasks.parser import parse_channel, parse_items
from tasks.formatters import format_console, format_json


def rss_parser(
    xml: str,
    limit: Optional[int] = None,
    json: bool = False,
) -> List[str]:
    """
    RSS parser.

    Args:
        xml: XML document as a string.
        limit: Number of the news to return. if None, returns all news.
        json: If True, format output as JSON.

    Returns:
        List of strings.
        Which then can be printed to stdout or written to file as a separate lines.

    Examples:
        >>> xml = (
        ...     '<rss><channel><title>Some RSS Channel</title>'
        ...     '<link>https://some.rss.com</link>'
        ...     '<description>Some RSS Channel</description>'
        ...     '</channel></rss>'
        ... )
        >>> rss_parser(xml)
        ['Feed: Some RSS Channel', 'Link: https://some.rss.com', 'Description: Some RSS Channel']
        >>> print("\\n".join(rss_parser(xml)))
        Feed: Some RSS Channel
        Link: https://some.rss.com
        Description: Some RSS Channel
    """
    try:
        root = fromstring(xml)
    except Exception as e:
        raise InvalidXMLError(f"Invalid XML: {e}") from e

    channel = root.find('channel')
    if channel is None:
        raise InvalidRSSError("No <channel> element found in RSS feed")

    channel_data = parse_channel(channel)
    items = parse_items(channel, limit)

    if json:
        return format_json(channel_data, items)
    return format_console(channel_data, items)


def main(argv: Optional[Sequence] = None):
    """
    The main function of your task.
    """
    parser = ArgumentParser(
        prog="rss_reader",
        description="Pure Python command-line RSS reader.",
    )
    parser.add_argument("source", help="RSS URL", type=str, nargs="?")
    parser.add_argument(
        "--json", help="Print result as JSON in stdout", action="store_true"
    )
    parser.add_argument(
        "--limit", help="Limit news topics if this parameter provided", type=int
    )

    args = parser.parse_args(argv)
    response = requests.get(args.source)
    response.encoding = response.apparent_encoding
    xml = response.text
    try:
        print("\n".join(rss_parser(xml, args.limit, args.json)))
        return 0
    except Exception as e:
        raise UnhandledException(e)


if __name__ == "__main__":
    main()
