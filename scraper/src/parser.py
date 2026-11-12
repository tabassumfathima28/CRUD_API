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


def parse_book_detail(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> dict[str, str | None]:
    """Extract the eight raw fields from one book detail page."""
    soup = BeautifulSoup(html, "html.parser")
    title = soup.select_one("div.product_main h1")
    price = soup.select_one("div.product_main .price_color")
    availability = soup.select_one("div.product_main .availability")
    rating = soup.select_one("div.product_main p.star-rating")
    description = soup.select_one("#product_description + p")

    rating_classes = rating.get("class", []) if rating else []
    rating_text = next(
        (class_name for class_name in rating_classes if class_name != "star-rating"),
        None,
    )

    return {
        "title": title.get_text(strip=True) if title else None,
        "product_url": product_url,
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": (
            availability.get_text(" ", strip=True) if availability else None
        ),
        "rating_text": rating_text,
        "description": (
            description.get_text(" ", strip=True) if description else None
        ),
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
