"""HTML parsing helpers for Books to Scrape pages."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_catalogue_page(
    html: str,
    catalogue_url: str,
) -> tuple[list[str], str | None]:
    """Return absolute book links and the absolute next-catalogue URL."""
    soup = BeautifulSoup(html, "html.parser")
    book_urls = [
        urljoin(catalogue_url, anchor["href"])
        for anchor in soup.select("article.product_pod h3 a[href]")
    ]

    next_link = soup.select_one("ul.pager li.next a[href]")
    next_url = (
        urljoin(catalogue_url, next_link["href"])
        if next_link is not None
        else None
    )
    return book_urls, next_url
