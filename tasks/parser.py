"""XML parsing for RSS 2.0 feeds."""

from html import unescape


CHANNEL_FIELDS = [
    'title', 'link', 'lastBuildDate', 'pubDate',
    'language', 'managingEditor', 'description',
]

ITEM_FIELDS = ['title', 'author', 'pubDate', 'link', 'description']


def get_text(elem):
    """Extract and clean text content from an XML element."""
    if elem is None:
        return None
    text = ''.join(elem.itertext()).strip()
    return unescape(text) if text else None


def parse_categories(parent):
    """Parse all <category> child elements and return a list."""
    categories = []
    for cat in parent.findall('category'):
        text = get_text(cat)
        if text:
            categories.append(text)
    return categories if categories else None


def parse_channel(channel):
    """Parse channel-level fields from the RSS channel element."""
    data = {}
    for field in CHANNEL_FIELDS:
        value = get_text(channel.find(field))
        if value:
            data[field] = value

    categories = parse_categories(channel)
    if categories:
        data['category'] = categories

    return data


def parse_items(channel, limit):
    """Parse <item> elements from the channel, applying limit."""
    items = []
    for item_elem in channel.findall('item'):
        item = {}
        for field in ITEM_FIELDS:
            value = get_text(item_elem.find(field))
            if value:
                item[field] = value

        categories = parse_categories(item_elem)
        if categories:
            item['category'] = categories

        items.append(item)

    if limit is not None:
        items = items[:limit]
    return items
