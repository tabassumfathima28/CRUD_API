# CRUD API with PostgreSQL

A simple Task CRUD API built using FastAPI and PostgreSQL.

## Features

- Create tasks
- Read all tasks
- Read a single task
- Update tasks
- Delete tasks
- PostgreSQL database persistence
- Automatic database and table creation
- Initial seed data

## Technologies

- Python
- FastAPI
- PostgreSQL
- Pydantic
- Uvicorn

## Database

The application connects to PostgreSQL using `DATABASE_URL`. On startup, it creates the `tasks` table if needed and seeds three example tasks only when the table is empty. The SQL queries use parameters for user-provided values.

Keep database credentials in `.env`; do not commit that file. `.env.example` documents the variables needed for local setup.

## How to Run

Build and start the API and PostgreSQL database with Docker Compose:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Compose waits for PostgreSQL to pass its health check before starting the API, and the `taskdata` volume preserves database data across container restarts.

To run the API directly with Python, install the dependencies and provide a PostgreSQL `DATABASE_URL`:

```bash
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open Swagger UI:

```text
http://localhost:8000/docs
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| GET | `/tasks` | Get all tasks |
| GET | `/tasks/{task_id}` | Get one task |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/{task_id}` | Update a task |
| DELETE | `/tasks/{task_id}` | Delete a task |

## Example SQL Query

```sql
SELECT * FROM tasks WHERE done = TRUE;
```

This returns all completed tasks.
