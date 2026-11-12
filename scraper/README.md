# FlyRank A9: The Polite Scraper

A small, modular Python scraper for the first three catalogue pages of Books
to Scrape. It follows the site's pagination, fetches each discovered book page,
validates the extracted data, and writes valid records, invalid-record
diagnostics, and a measured run report.

## Target Classification

- **Target website:** https://books.toscrape.com/
- **Why it is suitable:** The https://toscrape.com/ landing page describes
  Books to Scrape as a fictional bookstore intended for beginner scraping
  practice and technology validation. It states the catalogue is paginated,
  has 20 items per page, and does not require JavaScript.
- **Scope:** Only the first three catalogue pages and the book detail pages
  linked from them (approximately 60 books). Pagination is discovered from
  each page's actual next-page link; book URLs are not hardcoded.
- **Information collected:** title, product_url, price_text,
  availability_text, rating_text, description, source_page, fetched_at, and
  normalized price_gbp.
- **robots.txt finding:** Checked
  https://books.toscrape.com/robots.txt on 2026-11-12. The server returned
  HTTP 404 with a 153-byte HTML response containing “404 Not Found” and
  “nginx/1.21.6”; no robots.txt directives were provided. A missing
  robots.txt is not permission by itself. This assignment's limited target is
  chosen because the toscrape.com landing page explicitly presents it as a
  scraping sandbox.
- **Ethical limitations:** Recheck the target's terms and rules before running.
  Keep the scope to the first three catalogue pages and their product pages,
  use the identifiable client, cache HTML, wait between network requests, and
  stop if the site's rules or access behavior change.

I will not reuse this code on another site without checking its rules and terms first.

## Objective

1. Download only catalogue pages one through three by following their
   pagination links.
2. Discover and deduplicate the books linked from those pages.
3. Extract the eight raw fields from each book detail page.
4. Validate every record and convert its pound price into numeric
   `price_gbp`.
5. Continue after per-page failures and report actual run statistics.

## Technology

- Python
- `requests` for HTTP
- BeautifulSoup (`beautifulsoup4`) for HTML parsing
- Pydantic for record validation
- `pytest` for tests

The site's required data is present in the HTML returned by the server, so a
browser is not required. Browser automation would add unnecessary complexity
and cost for this static catalogue.

## Project structure

```text
scraper/
  README.md
  .gitignore
  requirements.txt
  __init__.py
  src/
    __init__.py
    main.py
    scraper.py
    parser.py
    models.py
    utils.py
  tests/
    __init__.py
    test_failure.py
    test_models.py
    test_parser.py
    test_utils.py
  cache/                 # locally cached HTML; ignored by Git
  output/
    sample-books.json    # small real sample, when a live run succeeds
    run-report-example.json
```

## Install and run

From the repository root:

```bash
python -m pip install -r scraper/requirements.txt
python -m scraper.src.main
```

The scraper always processes at most three catalogue pages. It reports the
catalogue/discovery counts, prints one complete raw record as an example, and
then reports detail, valid, invalid, and failed-page totals. Do not delete the
cache if you want to avoid downloading pages again.

## Output files

- `scraper/cache/`: downloaded HTML. Cache hits do not make a network request
  and do not incur the request delay. The directory is ignored by Git.
- `scraper/output/books.json`: validated records only.
- `scraper/output/errors.json`: raw invalid records and their Pydantic error
  locations/messages. Invalid records are never written to `books.json`.
- `scraper/output/run-report.json`: measured counts, elapsed time, and failed
  page URLs/reasons, including when a page fails.
- `scraper/output/sample-books.json`: a small sample copied from a successful
  live run when available. The checked-in sample omits the description text;
  the full field is still produced in the local `books.json` output.
- `scraper/output/run-report-example.json`: an actual run report copied from a
  completed run, not fabricated.

## Final data schema

Each item in `books.json` has these nine fields:

| Field | Meaning |
|---|---|
| `title` | Book title from the detail page |
| `product_url` | Absolute product page URL |
| `price_text` | Original price text, such as `£51.77` |
| `availability_text` | Original availability text |
| `rating_text` | Rating label from the page, such as `Three` |
| `description` | Description text, or `null` when absent |
| `source_page` | Catalogue page where the product was discovered |
| `fetched_at` | ISO 8601 UTC timestamp for the detail-page retrieval |
| `price_gbp` | Numeric GBP price, such as `51.77` |

Product URL identity is canonicalized for duplicate detection; the original
extracted URL is kept in `product_url`.

## Politeness and scope

- Identifiable User-Agent:
  `FlyRankInternshipA9/1.0 (+https://github.com/tabassumfathima28/CRUD_API)`.
- A 15-second request timeout and HTTP status checking before parsing.
- At least 0.5 seconds between actual requests; timeout and HTTP 5xx failures
  are retried once after a delay.
- HTTP 403 and 404 responses are not retried.
- Successful HTML responses are cached; cache hits do not sleep or request the
  site again.
- The scraper follows no more than three catalogue pages and does not crawl
  beyond their discovered products.

## Error handling and limitations

Failed detail URLs and reasons are logged and recorded in the run report; a
failed page does not stop remaining books from being processed. Malformed or
incomplete detail data is recorded in `errors.json`. Catalogue fetch failure
ends discovery because the next link cannot be trusted, but output files and a
run report are still written.

The HTML layout can change, which may cause records to be rejected until the
parser is updated. The robots.txt URL returned 404 when checked, so this
project relies on the target's stated scraping-sandbox purpose and its narrow
educational scope; that finding should be rechecked before a later run.

## Testing

From the repository root:

```bash
python -m pytest -q
```

Tests use local HTML and mocked HTTP responses. They do not depend on repeated
live requests to the target.

## Actual run evidence

The example below is copied from `output/run-report-example.json`; its values
are measurements from that run, not expected or fabricated counts:

```json
{
  "start_time": "2026-11-12T03:32:33.678913+00:00",
  "duration_seconds": 32.574,
  "catalogue_pages": 3,
  "detail_pages": 60,
  "pages_fetched": 63,
  "cache_hits": 0,
  "discovered_urls": 60,
  "unique_urls": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": []
}
```

This sample and `output/run-report-example.json` were generated from the same
successful live run; the report file includes all measured fields.

## Ethics

Prefer an official API when one is available. Never bypass login systems,
paywalls, or access restrictions. Collect only the information needed for this
assignment. Check the target site's terms and rules before scraping, and do
not transfer this scraper's behavior to another site without reviewing that
site independently.
