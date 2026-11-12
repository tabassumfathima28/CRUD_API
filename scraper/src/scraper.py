"""Catalogue discovery and book detail collection pipeline."""

from dataclasses import dataclass

from scraper.src.parser import parse_catalogue_page
from scraper.src.utils import FetchedPage, HttpFetcher


START_URL = "https://books.toscrape.com/"
CATALOGUE_PAGE_LIMIT = 3


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
