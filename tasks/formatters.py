"""Output formatters for parsed RSS data."""

import json


CHANNEL_LABELS = {
    'title': 'Feed',
    'link': 'Link',
    'lastBuildDate': 'Last Build Date',
    'pubDate': 'Publish Date',
    'language': 'Language',
    'category': 'Categories',
    'managingEditor': 'Editor',
    'description': 'Description',
}

ITEM_LABELS = {
    'title': 'Title',
    'author': 'Author',
    'pubDate': 'Published',
    'link': 'Link',
    'category': 'Categories',
}

CHANNEL_DISPLAY_ORDER = [
    'title', 'link', 'lastBuildDate', 'pubDate',
    'language', 'category', 'managingEditor', 'description',
]

ITEM_DISPLAY_ORDER = ['title', 'author', 'pubDate', 'link', 'category']

ITEM_JSON_ORDER = [
    'title', 'author', 'pubDate', 'link', 'category', 'description',
]


def _format_category(value):
    """Join a category list into a comma-separated string."""
    return ', '.join(value)


def format_console(channel_data, items):
    """Format parsed data as console output lines."""
    lines = []

    for field in CHANNEL_DISPLAY_ORDER:
        if field in channel_data:
            value = channel_data[field]
            if field == 'category':
                value = _format_category(value)
            lines.append(f"{CHANNEL_LABELS[field]}: {value}")

    for item in items:
        lines.append('')

        for field in ITEM_DISPLAY_ORDER:
            if field in item:
                value = item[field]
                if field == 'category':
                    value = _format_category(value)
                lines.append(f"{ITEM_LABELS[field]}: {value}")

        if 'description' in item:
            lines.append('')
            lines.append(item['description'])

    return lines


def format_json(channel_data, items):
    """Format parsed data as JSON output lines."""
    output = {}

    for field in CHANNEL_DISPLAY_ORDER:
        if field in channel_data:
            output[field] = channel_data[field]

    if items:
        output['items'] = []
        for item in items:
            output_item = {}
            for field in ITEM_JSON_ORDER:
                if field in item:
                    output_item[field] = item[field]
            output['items'].append(output_item)

    json_str = json.dumps(output, indent=2, ensure_ascii=False)
    return json_str.split('\n')
