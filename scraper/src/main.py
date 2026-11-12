"""Command-line entry point for the bounded Books to Scrape assignment."""

import logging

from scraper.src.scraper import run_scraper


def main() -> None:
    logging.basicConfig(
        level=logging.ERROR,
        format="%(levelname)s %(name)s: %(message)s",
    )
    report = run_scraper()
    print(f"detail_pages={report['detail_pages']}")
    print(f"valid_records={report['valid_records']}")
    print(f"invalid_records={report['invalid_records']}")
    print(f"failed_pages={len(report['failed_pages'])}")


if __name__ == "__main__":
    main()
