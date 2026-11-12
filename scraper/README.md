# FlyRank A9: The Polite Scraper

## Target Classification

- **Target:** https://books.toscrape.com/
- **Suitability:** The toscrape.com landing page describes Books to Scrape as a fictional bookstore intended for beginner scraping practice and technology validation. It states the catalogue is paginated, has 20 items per page, and does not require JavaScript.
- **Scope:** Only the first three catalogue pages and the books linked from those pages (expected: 60 books). The scraper follows each catalogue page's own next-page link.
- **Information collected:** title, product_url, price_text, availability_text, rating_text, description, source_page, fetched_at, and normalized price_gbp.
- **robots.txt finding:** Checked https://books.toscrape.com/robots.txt on 2026-11-12. The server returned HTTP 404 and a 153-byte HTML response containing “404 Not Found” and “nginx/1.21.6”; no robots.txt directives were provided. A missing robots.txt is not permission by itself. This assignment's limited target is chosen because the toscrape.com landing page explicitly presents it as a scraping sandbox.
- **Ethical limitations:** Keep requests to the documented three catalogue pages and their product pages, use the identifiable client, cache HTML, wait between network requests, and stop if site rules or access behavior change. Do not reuse the code against unrelated sites without reviewing their rules and terms.

I will not reuse this code on another site without checking its rules and terms first.

## Assignment objective

Discover the first three catalogue pages, extract the listed product data from
their book detail pages, validate and normalize records, and save successful
records, invalid records, and an honest run report separately.

## Project layout

```text
scraper/
  src/
  tests/
  cache/
  output/
```

The cache and generated full-run JSON files are local runtime data. The
`cache/` directory is ignored by Git.
