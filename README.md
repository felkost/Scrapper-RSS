# Scrapper

### Project Structure

```
scrapper-student-template/
├── tasks/
│   ├── __init__.py
│   ├── exceptions.py    # Custom exception hierarchy
│   ├── parser.py        # XML parsing — extract data from RSS feed
│   ├── formatters.py    # Output formatting — console and JSON
│   └── rss_reader.py    # Orchestrator + CLI entry point
├── tests/
│   ├── __init__.py
│   ├── test_exceptions.py   # Exception hierarchy tests
│   ├── test_parser.py       # XML parsing tests
│   ├── test_formatters.py   # Output formatting tests
│   └── test_rss_reader.py   # Integration + CLI tests
├── requirements.txt     # Dependencies: requests, pytest, pytest-cov
└── README.md
```

Each module has a single responsibility:

| Module | Task | Contents |
|--------|------|----------|
| `exceptions.py` | Define error types | `UnhandledException`, `InvalidXMLError`, `InvalidRSSError` |
| `parser.py` | Extract data from XML | `get_text()`, `parse_categories()`, `parse_channel()`, `parse_items()` |
| `formatters.py` | Convert data to output | `format_console()`, `format_json()` + label constants |
| `rss_reader.py` | Coordinate and run | `rss_parser()` orchestrates parsing + formatting, `main()` handles CLI |

### Architecture

Each layer lives in its own module. Data flows top-down through clearly defined interfaces:

```
┌──────────────────────────────────────────────────────┐
│  CLI Layer                          [rss_reader.py]  │
│  main() — argument parsing, HTTP request, output     │
└───────────────────────┬──────────────────────────────┘
                        │  xml: str, limit, json
┌───────────────────────▼──────────────────────────────┐
│  Orchestrator                       [rss_reader.py]  │
│  rss_parser() — validates XML, coordinates parsing   │
│                 and formatting                       │
└──────┬────────────────────────────────────┬──────────┘
       │                                    │
┌──────▼───────────────────────┐  ┌─────────▼──────────────────────┐
│  Parsing Layer  [parser.py]  │  │  Formatting Layer              │
│                              │  │              [formatters.py]   │
│  get_text()                  │  │                                │
│  parse_categories()          │  │  format_console() → List[str]  │
│  parse_channel() → dict      │  │  format_json()    → List[str]  │
│  parse_items()   → list      │  │                                │
└──────────────────────────────┘  └────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  Exceptions                     [exceptions.py]      │
│  UnhandledException → InvalidXMLError                │
│                     → InvalidRSSError                │
└──────────────────────────────────────────────────────┘
```

**Key design decisions:**

| Decision | Reason |
|----------|--------|
| Categories stored as `list` internally | Console needs `", ".join()`, JSON needs a native array `["a", "b"]` |
| `"items"` key omitted from JSON when no items exist | Tests expect no empty `"items": []` for item-less channels |
| `_get_text()` uses `itertext()` + `html.unescape()` | Handles CDATA sections, nested HTML, and encoded entities (`&#39;` → `'`) |
| `response.encoding = response.apparent_encoding` | Prevents `requests` from defaulting to ISO-8859-1 for `text/xml` content |
| Field order defined by list constants | Single source of truth for the required output order |
| Missing fields silently skipped | Only present XML tags appear in output — no empty labels |

### Exception Hierarchy

```
UnhandledException          ← base class (from template)
├── InvalidXMLError         ← raised when XML cannot be parsed
└── InvalidRSSError         ← raised when <channel> element is missing
```

### Execution Flow

#### Use Case 1: Console Output

```
User runs:  python rss_reader.py "https://news.yahoo.com/rss" --limit 2

1. main() parses CLI arguments
   → source="https://news.yahoo.com/rss", limit=2, json=False

2. main() fetches the RSS feed via HTTP
   → fixes encoding via apparent_encoding
   → passes XML string to rss_parser()

3. rss_parser() validates XML with fromstring()
   → finds <channel> element

4. _parse_channel() extracts channel fields:
   → iterates CHANNEL_FIELDS in order
   → calls _get_text() for each field (unescape entities)
   → calls _parse_categories() for <category> tags → list

5. _parse_items() extracts <item> elements:
   → parses each item's fields + categories
   → applies limit: items = items[:2]

6. _format_console() builds output lines:
   → channel fields with labels (Feed:, Link:, etc.)
   → blank line separator between items
   → item fields stuck together, description on separate line

7. main() joins lines with "\n" and prints to stdout
```

#### Use Case 2: JSON Output

```
User runs:  python rss_reader.py "https://news.yahoo.com/rss" --json --limit 1

Steps 1-5 are identical to Use Case 1.

6. _format_json() builds a dict:
   → channel fields with original XML tag names as keys
   → categories remain as a native list (not comma-joined)
   → "items" key only added if items exist
   → json.dumps(indent=2, ensure_ascii=False)
   → splits JSON string into lines

7. main() joins lines with "\n" and prints to stdout
```

#### Use Case 3: Programmatic Usage (Testing)

```python
from tasks.rss_reader import rss_parser

xml = "<rss><channel>...</channel></rss>"
lines = rss_parser(xml, limit=5, json=False)
# No HTTP request — works directly with XML string
```

### Usage Examples

#### Help

```shell
$ python tasks/rss_reader.py --help
usage: rss_reader [-h] [--json] [--limit LIMIT] [source]

Pure Python command-line RSS reader.

positional arguments:
  source         RSS URL

options:
  -h, --help     show this help message and exit
  --json         Print result as JSON in stdout
  --limit LIMIT  Limit news topics if this parameter provided
```

#### Console Output (default)

```shell
$ python tasks/rss_reader.py "https://news.yahoo.com/rss" --limit 2
```

Output:

```
Feed: Yahoo News - Latest News & Headlines
Link: https://news.yahoo.com/rss
Last Build Date: Sun, 20 Oct 2019 04:21:44 +0300
Language: en-us
Description: Yahoo news description

Title: Nestor heads into Georgia after tornados damage Florida
Published: Sun, 20 Oct 2019 04:21:44 +0300
Link: https://news.yahoo.com/wet-weekend-tropical-storm-warnings-131131925.html

Nestor raced across Georgia as a post-tropical cyclone late Saturday...

Title: Some Other Title
Published: Sun, 20 Oct 2019 04:21:44 +0300
Link: https://some.other.link/some-other-news

Some other new cool information.
```

#### JSON Output

```shell
$ python tasks/rss_reader.py "https://news.yahoo.com/rss" --json --limit 1
```

Output:

```json
{
  "title": "Yahoo News - Latest News & Headlines",
  "link": "https://news.yahoo.com/rss",
  "lastBuildDate": "Sun, 20 Oct 2019 04:21:44 +0300",
  "language": "en-us",
  "description": "Yahoo news description",
  "items": [
    {
      "title": "Nestor heads into Georgia after tornados damage Florida",
      "pubDate": "Sun, 20 Oct 2019 04:21:44 +0300",
      "link": "https://news.yahoo.com/wet-weekend-tropical-storm-warnings-131131925.html",
      "description": "Nestor raced across Georgia as a post-tropical cyclone late Saturday..."
    }
  ]
}
```

#### All News (no limit)

```shell
$ python tasks/rss_reader.py "https://news.yahoo.com/rss"
```

Returns all available items from the feed.

#### Limit Larger Than Feed

```shell
$ python tasks/rss_reader.py "https://news.yahoo.com/rss" --limit 9999
```

Returns all available items (slice beyond list length returns the full list).

### Installation

```shell
pip install -r requirements.txt
```

The only runtime dependency is `requests`. Testing dependencies are `pytest` and `pytest-cov`. All other imports are part of the Python standard library.

### Testing

The test suite mirrors the source module structure — one test file per module:

| Test file | Module under test | What is tested |
|-----------|-------------------|----------------|
| `test_exceptions.py` | `exceptions.py` | Inheritance chain, catching subclasses as base type |
| `test_parser.py` | `parser.py` | Text extraction, entity decoding, category parsing, channel/item parsing, limit behavior |
| `test_formatters.py` | `formatters.py` | Console label mapping, field order, JSON structure, categories format, indent |
| `test_rss_reader.py` | `rss_reader.py` | End-to-end parsing, JSON/console modes, error handling, CLI with mocked HTTP |

#### Run all tests

```shell
python -m pytest tests/ -v
```

#### Run tests with coverage report

```shell
python -m pytest tests/ --cov=tasks --cov-report=term-missing
```

#### Run a specific test module

```shell
python -m pytest tests/test_parser.py -v
```

#### Coverage summary

```
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
tasks/__init__.py         0      0   100%
tasks/exceptions.py       6      0   100%
tasks/formatters.py      43      0   100%
tasks/parser.py          40      0   100%
tasks/rss_reader.py      36      3    92%   84-85, 89
---------------------------------------------------
TOTAL                   125      3    98%
```

The 3 uncovered lines are:
- Lines 84-85: `except` branch in `main()` — only reachable when `rss_parser()` raises during a live HTTP call
- Line 89: `if __name__ == "__main__"` guard — not executed during imports

**75 tests, 98% coverage.**
