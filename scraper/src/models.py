"""Validated book records and canonical product URL helpers."""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable
from decimal import Decimal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_PRICE_PATTERN = re.compile(r"\s*£\s*(\d+(?:\.\d{1,2})?)\s*")


def parse_price_gbp(price_text: str | None) -> float:
    """Convert a raw pound price such as £51.77 into a numeric amount."""
    if not isinstance(price_text, str):
        raise ValueError("price_text must be a GBP amount such as £51.77")
    match = _PRICE_PATTERN.fullmatch(price_text)
    if match is None:
        raise ValueError("price_text must be a GBP amount such as £51.77")
    return float(Decimal(match.group(1)))


def canonical_product_url(product_url: str) -> str:
    """Normalize URL case, dot segments, trailing slash, query, and fragment."""
    parts = urlsplit(product_url.strip())
    scheme = parts.scheme.lower()
    hostname = parts.hostname
    if scheme not in {"http", "https"} or not hostname:
        raise ValueError("product_url must be an absolute HTTP or HTTPS URL")
    if parts.username or parts.password:
        raise ValueError("product_url cannot contain user credentials")

    hostname = hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    port = parts.port
    if port is not None and not (
        (scheme == "http" and port == 80)
        or (scheme == "https" and port == 443)
    ):
        hostname = f"{hostname}:{port}"

    path = posixpath.normpath(parts.path or "/")
    if not path.startswith("/"):
        path = f"/{path}"
    return urlunsplit((scheme, hostname, path, "", ""))


class BookRecord(BaseModel):
    """The eight extracted fields plus a normalized numeric GBP price."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    product_url: str = Field(min_length=1)
    price_text: str = Field(min_length=1)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: str | None = None
    source_page: str = Field(min_length=1)
    fetched_at: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)

    @model_validator(mode="before")
    @classmethod
    def derive_price_gbp(cls, values):
        if isinstance(values, dict) and "price_gbp" not in values:
            values = {
                **values,
                "price_gbp": parse_price_gbp(values.get("price_text", "")),
            }
        return values

    @field_validator("title", "price_text", "availability_text", "rating_text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field cannot be blank")
        return value

    @field_validator("product_url", "source_page")
    @classmethod
    def require_absolute_http_url(cls, value: str) -> str:
        try:
            canonical_product_url(value)
        except ValueError as exc:
            raise ValueError(
                "value must be an absolute HTTP or HTTPS URL without credentials"
            ) from exc
        return value

    @field_validator("fetched_at")
    @classmethod
    def require_iso_timestamp(cls, value: str) -> str:
        from datetime import datetime

        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("fetched_at must be an ISO 8601 timestamp") from exc
        return value


def deduplicate_records(
    records: Iterable[BookRecord],
) -> list[BookRecord]:
    """Keep the first valid record for each canonical product URL."""
    unique_records: list[BookRecord] = []
    seen_urls: set[str] = set()
    for record in records:
        identity = canonical_product_url(record.product_url)
        if identity not in seen_urls:
            seen_urls.add(identity)
            unique_records.append(record)
    return unique_records
