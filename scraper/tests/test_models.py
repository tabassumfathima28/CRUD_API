import pytest
from pydantic import ValidationError

from scraper.src.models import (
    BookRecord,
    canonical_product_url,
    deduplicate_records,
    parse_price_gbp,
)


def _raw_record(**overrides):
    record = {
        "title": "A Book",
        "product_url": "https://books.toscrape.com/catalogue/a-book/index.html",
        "price_text": "£51.77",
        "availability_text": "In stock (22 available)",
        "rating_text": "Three",
        "description": None,
        "source_page": "https://books.toscrape.com/",
        "fetched_at": "2026-11-12T03:00:00+00:00",
    }
    record.update(overrides)
    return record


def test_price_normalization_preserves_raw_price_text():
    record = BookRecord.model_validate(_raw_record())

    assert parse_price_gbp("£51.77") == 51.77
    assert record.price_text == "£51.77"
    assert record.price_gbp == 51.77
    assert len(record.model_dump()) == 9


def test_optional_description_and_invalid_price_validation():
    record = BookRecord.model_validate(_raw_record(description=None))
    assert record.description is None

    with pytest.raises(ValidationError):
        BookRecord.model_validate(_raw_record(price_text="price unavailable"))


def test_required_fields_are_validated():
    with pytest.raises(ValidationError) as error:
        BookRecord.model_validate(_raw_record(title=None))

    assert any(item["loc"] == ("title",) for item in error.value.errors())


def test_product_url_canonicalization_and_duplicate_removal():
    first = BookRecord.model_validate(
        _raw_record(
            product_url=(
                "HTTPS://Books.ToScrape.com/catalogue/./a-book/index.html"
                "?ref=home#details"
            )
        )
    )
    duplicate = BookRecord.model_validate(
        _raw_record(
            product_url="https://books.toscrape.com/catalogue/a-book/index.html"
        )
    )

    assert canonical_product_url(first.product_url) == canonical_product_url(
        duplicate.product_url
    )
    assert deduplicate_records([first, duplicate]) == [first]
