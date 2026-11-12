from unittest.mock import Mock

import pytest
import requests

from scraper.src.utils import FetchError, HttpFetcher, USER_AGENT


class FakeResponse:
    def __init__(self, content=b"<html>fixture</html>", status_code=200):
        self.content = content
        self.text = content.decode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            response = Mock(status_code=self.status_code)
            raise requests.HTTPError(
                f"HTTP {self.status_code}",
                response=response,
            )


def test_fetch_sets_user_agent_timeout_and_caches_response(tmp_path, capsys):
    session = Mock()
    session.get.return_value = FakeResponse()
    fetcher = HttpFetcher(
        tmp_path / "cache",
        session=session,
        sleep=Mock(),
        monotonic=Mock(return_value=100.0),
    )

    first = fetcher.fetch(
        "https://books.toscrape.com/",
        cache_name="catalogue-page-1.html",
    )
    second = fetcher.fetch(
        "https://books.toscrape.com/",
        cache_name="catalogue-page-1.html",
    )

    assert first.html == second.html == "<html>fixture</html>"
    assert first.cache_hit is False
    assert second.cache_hit is True
    session.get.assert_called_once_with(
        "https://books.toscrape.com/",
        headers={"User-Agent": USER_AGENT},
        timeout=15.0,
    )
    assert (tmp_path / "cache" / "catalogue-page-1.html").is_file()
    output = capsys.readouterr().out
    assert "FETCH [https://books.toscrape.com/]" in output
    assert "Saved cache/catalogue-page-1.html" in output
    assert "CACHE HIT catalogue-page-1.html" in output
    assert "response_size_bytes=20" in output
    assert "<html>fixture</html>" not in output


def test_fetch_checks_http_status_before_caching(tmp_path):
    session = Mock()
    session.get.return_value = FakeResponse(status_code=404)
    fetcher = HttpFetcher(tmp_path, session=session, sleep=Mock())

    with pytest.raises(FetchError) as error:
        fetcher.fetch("https://example.test/missing", retries=1)

    assert error.value.status_code == 404
    session.get.assert_called_once()
    assert list(tmp_path.iterdir()) == []


def test_fetch_retries_timeout_once_after_a_delay(tmp_path):
    session = Mock()
    session.get.side_effect = [
        requests.Timeout("slow response"),
        FakeResponse(),
    ]
    sleep = Mock()
    fetcher = HttpFetcher(tmp_path, session=session, sleep=sleep)

    result = fetcher.fetch(
        "https://example.test/page",
        cache_name="page.html",
        retries=1,
    )

    assert result.html == "<html>fixture</html>"
    assert session.get.call_count == 2
    assert sleep.call_args_list[0].args == (0.5,)
