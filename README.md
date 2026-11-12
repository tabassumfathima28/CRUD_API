# FlyRank Internship Backend Track

A collection of backend development assignments completed as part of the FlyRank Internship Backend Track, using Python.

This repository contains REST API development, database integration, authentication, containerization, and web scraping projects.

## Projects

### A1–A4: CRUD API with Supabase Authentication

A FastAPI backend combining CRUD operations, PostgreSQL database integration, Docker Compose, and Supabase authentication.

**Technologies**
- Python 3.14
- FastAPI
- Uvicorn
- SQLite and PostgreSQL
- Psycopg
- Supabase Auth
- Docker and Docker Compose
- Pytest

**Features**
- Create, read, update, and delete operations.
- Persistent database storage.
- User signup and login using Supabase Auth.
- JWT verification.
- Protected API endpoints.
- Reusable authentication dependency.
- Swagger UI documentation.
- Docker Compose configuration.

**Authentication endpoints**

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register a user |
| POST | `/auth/login` | Log in |
| POST | `/auth/logout` | Log out |
| GET | `/protected/profile` | Get authenticated user profile |
| GET | `/public/info` | Get public information |

API documentation is available at `/docs` when the application is running.

---

### A9: The Polite Scraper

A Python web scraper that collects book information from [Books to Scrape](https://books.toscrape.com/), a practice website designed for web scraping.

**Objective**

Download the first three catalogue pages, discover 60 unique books, visit their individual pages, extract information, normalize the data, validate records, and save the results as JSON.

**Technologies**
- Python
- Requests
- BeautifulSoup4
- Pydantic
- JSON
- Pytest

**Features**
- Catalogue discovery across the first three pages.
- Automatic pagination using the website's next-page links.
- Extraction of 60 unique book records.
- HTML caching to avoid unnecessary requests.
- Custom User-Agent identification.
- Request timeouts and HTTP status checking.
- Minimum 0.5-second delay between actual requests.
- GBP price normalization.
- Pydantic schema validation.
- Duplicate record detection.
- Individual page failure handling.
- Retry logic for timeouts and HTTP 5xx responses.
- Automated run reporting.

**Data collected**

Each validated book record contains:

| Field | Description |
|---|---|
| `title` | Book title |
| `product_url` | Book detail page URL |
| `price_text` | Original price text |
| `availability_text` | Availability information |
| `rating_text` | Original rating text |
| `description` | Book description, if available |
| `source_page` | Catalogue page where the book was discovered |
| `fetched_at` | Retrieval timestamp |
| `price_gbp` | Normalized numeric price in GBP |

**Project structure**

```text
scraper/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── scraper.py
│   ├── parser.py
│   ├── models.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_utils.py
│   └── test_failure.py
├── cache/
└── output/
    ├── books.json
    ├── errors.json
    └── run-report.json
```

Generated cache and full output files are kept locally and excluded from Git where appropriate. Sample records and a successful run-report example are included in the repository.

**Run the scraper**

From the repository root:

```bash
python -m pip install -r scraper/requirements.txt
python -m scraper.src.main
```

**Run tests**

```bash
python -m pytest -q
```

**Verified live run**

The successful live execution processed:

| Metric | Result |
|---|---:|
| Catalogue pages | 3 |
| Detail pages | 60 |
| Unique book URLs | 60 |
| Valid records | 60 |
| Invalid records | 0 |
| Failed pages | 0 |
| Network fetches | 63 |

A subsequent execution used the cached HTML pages.

See [`scraper/README.md`](scraper/README.md) for the detailed A9 implementation, installation instructions, execution evidence, and ethical scraping considerations.

---

## Testing

Automated tests are implemented using Pytest.

The final repository-wide test run completed with **32 passing tests**.

```bash
python -m pytest -q
```

## Ethical Considerations

The scraper is intentionally limited to a practice website.

- Use an official API whenever one is available.
- Check website rules and terms before scraping.
- Identify the scraper using an honest User-Agent.
- Avoid unnecessary requests.
- Respect access restrictions.
- Never bypass authentication systems or paywalls.
- Collect only the information required for the task.

I will not reuse this code on another site without checking its rules and terms first.

## Repository

GitHub: [tabassumfathima28/CRUD_API](https://github.com/tabassumfathima28/CRUD_API)

This repository documents the practical implementation of backend development concepts through the FlyRank Internship Backend Track.
