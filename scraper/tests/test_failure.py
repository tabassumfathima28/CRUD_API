import json

from scraper.src.scraper import START_URL, run_scraper
from scraper.src.utils import FetchError, FetchedPage


def test_failed_detail_does_not_prevent_valid_and_invalid_outputs(
    tmp_path,
    caplog,
):
    failed_url = "https://books.toscrape.com/catalogue/broken/index.html"
    invalid_url = "https://books.toscrape.com/catalogue/malformed/index.html"
    valid_url = "https://books.toscrape.com/catalogue/valid/index.html"
    catalogue_html = f"""
    <html><body>
      <article class="product_pod"><h3><a href="{failed_url}">broken</a></h3></article>
      <article class="product_pod"><h3><a href="{invalid_url}">malformed</a></h3></article>
      <article class="product_pod"><h3><a href="{valid_url}">valid</a></h3></article>
    </body></html>
    """

    class FixtureFetcher:
        def fetch(self, url, cache_name=None, retries=0):
            if url == START_URL:
                html = catalogue_html
            elif url == failed_url:
                raise FetchError(url, "simulated HTTP 503", 503)
            elif url == invalid_url:
                html = "<html><body><p>Malformed book page</p></body></html>"
            elif url == valid_url:
                html = _valid_book_html()
            else:
                raise AssertionError(f"Unexpected URL: {url}")
            return FetchedPage(
                html=html,
                cache_hit=False,
                response_size_bytes=len(html.encode("utf-8")),
                cache_filename=cache_name or "detail.html",
            )

    report = run_scraper(
        fetcher=FixtureFetcher(),
        output_dir=tmp_path / "output",
    )
    output_dir = tmp_path / "output"
    books = json.loads((output_dir / "books.json").read_text(encoding="utf-8"))
    errors = json.loads((output_dir / "errors.json").read_text(encoding="utf-8"))
    saved_report = json.loads(
        (output_dir / "run-report.json").read_text(encoding="utf-8")
    )

    assert [record["product_url"] for record in books] == [valid_url]
    assert books[0]["price_gbp"] == 51.77
    assert len(errors) == 1
    assert errors[0]["record"]["title"] is None
    assert errors[0]["errors"]
    assert report["catalogue_pages"] == 1
    assert report["detail_pages"] == 2
    assert report["discovered_urls"] == 3
    assert report["unique_urls"] == 3
    assert report["pages_fetched"] == 3
    assert report["valid_records"] == 1
    assert report["invalid_records"] == 1
    assert report["failed_pages"] == [
        {"url": failed_url, "reason": "simulated HTTP 503"}
    ]
    assert saved_report == report
    assert failed_url in caplog.text
    assert "simulated HTTP 503" in caplog.text


def test_failed_catalogue_still_writes_empty_outputs_and_run_report(tmp_path):
    class FailedCatalogueFetcher:
        def fetch(self, url, cache_name=None, retries=0):
            raise FetchError(url, "simulated timeout")

    output_dir = tmp_path / "output"
    report = run_scraper(
        fetcher=FailedCatalogueFetcher(),
        output_dir=output_dir,
    )

    assert report["catalogue_pages"] == 0
    assert report["failed_pages"] == [
        {"url": START_URL, "reason": "simulated timeout"}
    ]
    assert json.loads((output_dir / "books.json").read_text()) == []
    assert json.loads((output_dir / "errors.json").read_text()) == []
    assert json.loads((output_dir / "run-report.json").read_text()) == report


def _valid_book_html():
    return """
    <html><body>
      <div class="product_main">
        <h1>Valid Book</h1>
        <p class="price_color">£51.77</p>
        <p class="availability">In stock (2 available)</p>
        <p class="star-rating Three"></p>
      </div>
    </body></html>
    """
