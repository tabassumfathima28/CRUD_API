"""Catalogue discovery and book detail collection pipeline."""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from scraper.src.models import (
    BookRecord,
    canonical_product_url,
    deduplicate_records,
)
from scraper.src.parser import parse_catalogue_page
from scraper.src.parser import parse_book_detail
from scraper.src.utils import FetchError, FetchedPage, HttpFetcher


START_URL = "https://books.toscrape.com/"
CATALOGUE_PAGE_LIMIT = 3
PROJECT_DIR = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DiscoveredBook:
    url: str
    source_page: str


@dataclass(frozen=True)
class CatalogueDiscovery:
    books: list[DiscoveredBook]
    catalogue_pages: int
    discovered_urls: int
    pages_fetched: int
    cache_hits: int


def discover_books(
    fetcher: HttpFetcher,
    start_url: str = START_URL,
) -> CatalogueDiscovery:
    """Follow at most three actual next-page links and deduplicate books."""
    current_url: str | None = start_url
    books: list[DiscoveredBook] = []
    seen_urls: set[str] = set()
    discovered_urls = 0
    pages_fetched = 0
    cache_hits = 0
    catalogue_pages = 0

    for page_number in range(1, CATALOGUE_PAGE_LIMIT + 1):
        if current_url is None:
            break

        page: FetchedPage = fetcher.fetch(
            current_url,
            cache_name=f"catalogue-page-{page_number}.html",
            retries=1,
        )
        catalogue_pages += 1
        if page.cache_hit:
            cache_hits += 1
        else:
            pages_fetched += 1

        page_urls, next_url = parse_catalogue_page(page.html, current_url)
        discovered_urls += len(page_urls)
        for book_url in page_urls:
            if book_url not in seen_urls:
                seen_urls.add(book_url)
                books.append(
                    DiscoveredBook(
                        url=book_url,
                        source_page=current_url,
                    )
                )

        current_url = next_url

    print(f"catalogue_pages={catalogue_pages}")
    print(f"discovered={discovered_urls}")
    print(f"unique_urls={len(books)}")
    return CatalogueDiscovery(
        books=books,
        catalogue_pages=catalogue_pages,
        discovered_urls=discovered_urls,
        pages_fetched=pages_fetched,
        cache_hits=cache_hits,
    )


def run_scraper(
    fetcher: HttpFetcher | None = None,
    output_dir: Path | None = None,
    start_url: str = START_URL,
) -> dict[str, Any]:
    """Run the bounded scrape and persist records, errors, and measured stats."""
    fetcher = fetcher or HttpFetcher(PROJECT_DIR / "cache")
    output_dir = Path(output_dir or PROJECT_DIR / "output")
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = datetime.now(timezone.utc)
    monotonic_start = time.monotonic()
    report: dict[str, Any] = {
        "start_time": start_time.isoformat(),
        "duration_seconds": 0.0,
        "catalogue_pages": 0,
        "pages_fetched": 0,
        "cache_hits": 0,
        "discovered_urls": 0,
        "unique_urls": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "failed_pages": [],
    }
    valid_records: list[BookRecord] = []
    invalid_records: list[dict[str, Any]] = []
    seen_product_urls: set[str] = set()
    raw_example_printed = False

    try:
        try:
            discovery = discover_books(fetcher, start_url)
        except FetchError as exc:
            _record_failure(report, exc)
        else:
            report["catalogue_pages"] = discovery.catalogue_pages
            report["pages_fetched"] += discovery.pages_fetched
            report["cache_hits"] += discovery.cache_hits
            report["discovered_urls"] = discovery.discovered_urls
            report["unique_urls"] = len(discovery.books)

            for book in discovery.books:
                try:
                    page = fetcher.fetch(book.url, retries=1)
                except FetchError as exc:
                    _record_failure(report, exc)
                    continue

                if page.cache_hit:
                    report["cache_hits"] += 1
                else:
                    report["pages_fetched"] += 1

                raw_record = parse_book_detail(
                    page.html,
                    product_url=book.url,
                    source_page=book.source_page,
                    fetched_at=datetime.now(timezone.utc).isoformat(),
                )
                if not raw_example_printed:
                    print(
                        "example_raw_record="
                        + json.dumps(raw_record, ensure_ascii=False)
                    )
                    raw_example_printed = True

                product_url = raw_record["product_url"]
                if isinstance(product_url, str):
                    try:
                        identity = canonical_product_url(product_url)
                    except ValueError:
                        identity = None
                    if identity is not None and identity in seen_product_urls:
                        continue
                    if identity is not None:
                        seen_product_urls.add(identity)

                try:
                    record = BookRecord.model_validate(raw_record)
                except ValidationError as exc:
                    invalid_records.append(
                        {
                            "record": raw_record,
                            "errors": [
                                {
                                    "loc": list(error["loc"]),
                                    "msg": error["msg"],
                                    "type": error["type"],
                                }
                                for error in exc.errors()
                            ],
                        }
                    )
                    continue

                valid_records.append(record)
    finally:
        valid_records = deduplicate_records(valid_records)
        report["valid_records"] = len(valid_records)
        report["invalid_records"] = len(invalid_records)
        report["duration_seconds"] = round(
            max(0.0, time.monotonic() - monotonic_start),
            3,
        )
        _write_json(
            output_dir / "books.json",
            [record.model_dump(mode="json") for record in valid_records],
        )
        _write_json(output_dir / "errors.json", invalid_records)
        _write_json(output_dir / "run-report.json", report)

    return report


def _record_failure(report: dict[str, Any], error: FetchError) -> None:
    failure = {"url": error.url, "reason": error.reason}
    report["failed_pages"].append(failure)
    LOGGER.error("Failed to fetch %s: %s", error.url, error.reason)


def _write_json(path: Path, value: Any) -> None:
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)
