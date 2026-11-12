"""Polite HTTP fetching and local HTML caching."""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import requests


USER_AGENT = (
    "FlyRankInternshipA9/1.0 "
    "(+https://github.com/tabassumfathima28/CRUD_API)"
)


class FetchError(Exception):
    """A request or cached page could not be retrieved successfully."""

    def __init__(
        self,
        url: str,
        reason: str,
        status_code: int | None = None,
    ) -> None:
        self.url = url
        self.reason = reason
        self.status_code = status_code
        super().__init__(f"{url}: {reason}")


@dataclass(frozen=True)
class FetchedPage:
    html: str
    cache_hit: bool
    response_size_bytes: int
    cache_filename: str


class HttpFetcher:
    """Fetch pages with a delay, a descriptive User-Agent, and disk caching."""

    def __init__(
        self,
        cache_dir: Path,
        timeout: float = 15.0,
        delay_seconds: float = 0.5,
        session: requests.Session | None = None,
        sleep=time.sleep,
        monotonic=time.monotonic,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        if delay_seconds < 0.5:
            raise ValueError("delay_seconds must be at least 0.5")

        self.cache_dir = Path(cache_dir)
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.session = session or requests.Session()
        self._sleep = sleep
        self._monotonic = monotonic
        self._last_request_started: float | None = None

    def fetch(
        self,
        url: str,
        cache_name: str | None = None,
        retries: int = 0,
    ) -> FetchedPage:
        if retries < 0:
            raise ValueError("retries cannot be negative")

        filename = cache_name or self._cache_filename(url)
        if Path(filename).name != filename:
            raise ValueError("cache_name must be a filename, not a path")

        cache_path = self.cache_dir / filename
        if cache_path.is_file():
            cached_bytes = cache_path.read_bytes()
            html = cached_bytes.decode("utf-8")
            print(f"CACHE HIT {filename}")
            print(f"response_size_bytes={len(cached_bytes)}")
            return FetchedPage(
                html=html,
                cache_hit=True,
                response_size_bytes=len(cached_bytes),
                cache_filename=filename,
            )

        attempt = 0
        while True:
            self._wait_for_request_slot()
            print(f"FETCH [{url}]")
            self._last_request_started = self._monotonic()

            try:
                response = self.session.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=self.timeout,
                )
                response.raise_for_status()
            except requests.Timeout as exc:
                if attempt < retries:
                    attempt += 1
                    print(f"Retrying after timeout ({attempt}/{retries})")
                    self._sleep(self.delay_seconds)
                    continue
                raise FetchError(url, self._reason(exc)) from exc
            except requests.HTTPError as exc:
                status_code = (
                    exc.response.status_code
                    if exc.response is not None
                    else None
                )
                if (
                    status_code is not None
                    and 500 <= status_code <= 599
                    and attempt < retries
                ):
                    attempt += 1
                    print(
                        f"Retrying after HTTP {status_code} "
                        f"({attempt}/{retries})"
                    )
                    self._sleep(self.delay_seconds)
                    continue
                reason = f"HTTP {status_code}" if status_code else self._reason(exc)
                raise FetchError(url, reason, status_code) from exc
            except requests.RequestException as exc:
                raise FetchError(url, self._reason(exc)) from exc

            try:
                html = self._decode_response(response)
            except (LookupError, UnicodeDecodeError) as exc:
                raise FetchError(
                    url,
                    f"could not decode response: {self._reason(exc)}",
                ) from exc
            cached_bytes = html.encode("utf-8")
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            temporary_path = cache_path.with_suffix(cache_path.suffix + ".tmp")
            temporary_path.write_bytes(cached_bytes)
            temporary_path.replace(cache_path)

            response_size = len(response.content)
            print(f"Saved cache/{filename}")
            print(f"response_size_bytes={response_size}")
            return FetchedPage(
                html=html,
                cache_hit=False,
                response_size_bytes=response_size,
                cache_filename=filename,
            )

    def _wait_for_request_slot(self) -> None:
        if self._last_request_started is None:
            return
        elapsed = self._monotonic() - self._last_request_started
        remaining = self.delay_seconds - elapsed
        if remaining > 0:
            self._sleep(remaining)

    @staticmethod
    def _reason(error: Exception) -> str:
        return str(error) or type(error).__name__

    @staticmethod
    def _decode_response(response: requests.Response) -> str:
        content_type = response.headers.get("Content-Type", "")
        declared_charset = re.search(
            r"charset\s*=\s*[\"']?([A-Za-z0-9._-]+)",
            content_type,
            flags=re.IGNORECASE,
        )
        if declared_charset is not None:
            return response.content.decode(declared_charset.group(1))

        try:
            return response.content.decode("utf-8-sig")
        except UnicodeDecodeError:
            encoding = response.apparent_encoding or response.encoding
            if not encoding:
                raise
            return response.content.decode(encoding)

    @staticmethod
    def _cache_filename(url: str) -> str:
        path_stem = Path(urlsplit(url).path).stem or "page"
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", path_stem).strip("-")
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
        return f"{safe_stem[:48] or 'page'}-{digest}.html"
