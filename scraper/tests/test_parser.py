from scraper.src.parser import parse_catalogue_page
from scraper.src.scraper import CATALOGUE_PAGE_LIMIT, discover_books
from scraper.src.utils import FetchedPage


def test_catalogue_links_are_absolute_and_next_link_is_followable():
    html = """
    <html><body>
      <article class="product_pod">
        <h3><a href="book-one/index.html">Book one</a></h3>
      </article>
      <ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>
    </body></html>
    """

    book_urls, next_url = parse_catalogue_page(
        html,
        "https://books.toscrape.com/catalogue/page-1.html",
    )

    assert book_urls == [
        "https://books.toscrape.com/catalogue/book-one/index.html"
    ]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_discovery_follows_next_links_for_only_three_pages():
    catalogue_urls = [
        "https://books.toscrape.com/",
        "https://books.toscrape.com/catalogue/page-2.html",
        "https://books.toscrape.com/catalogue/page-3.html",
    ]
    html_by_url = {
        catalogue_urls[0]: _catalogue_html(
            ["catalogue/book-a/index.html"],
            "catalogue/page-2.html",
        ),
        catalogue_urls[1]: _catalogue_html(
            ["book-a/index.html", "book-b/index.html"],
            "page-3.html",
        ),
        catalogue_urls[2]: _catalogue_html(
            ["book-c/index.html"],
            "page-4.html",
        ),
    }

    class FixtureFetcher:
        def __init__(self):
            self.urls = []

        def fetch(self, url, cache_name=None):
            self.urls.append(url)
            return FetchedPage(
                html=html_by_url[url],
                cache_hit=False,
                response_size_bytes=len(html_by_url[url].encode("utf-8")),
                cache_filename=cache_name or "fixture.html",
            )

    fetcher = FixtureFetcher()
    result = discover_books(fetcher)

    assert CATALOGUE_PAGE_LIMIT == 3
    assert fetcher.urls == catalogue_urls
    assert result.catalogue_pages == 3
    assert result.discovered_urls == 4
    assert [book.url for book in result.books] == [
        "https://books.toscrape.com/catalogue/book-a/index.html",
        "https://books.toscrape.com/catalogue/book-b/index.html",
        "https://books.toscrape.com/catalogue/book-c/index.html",
    ]
    assert result.books[0].source_page == catalogue_urls[0]
    assert result.pages_fetched == 3
    assert result.cache_hits == 0


def _catalogue_html(book_paths: list[str], next_path: str) -> str:
    books = "".join(
        f'<article class="product_pod"><h3><a href="{path}">book</a></h3></article>'
        for path in book_paths
    )
    return (
        f"<html><body>{books}"
        f'<ul class="pager"><li class="next"><a href="{next_path}">next</a>'
        "</li></ul></body></html>"
    )
