# CRUD API with SQLite

A simple Task CRUD API built using FastAPI and SQLite.

## Features

- Create tasks
- Read all tasks
- Read a single task
- Update tasks
- Delete tasks
- SQLite database persistence
- Automatic database and table creation
- Initial seed data

## Technologies

- Python
- FastAPI
- SQLite
- Pydantic
- Uvicorn

## Why SQLite?

SQLite was used because it is lightweight, requires zero database server setup, and stores the complete database in a single file. Unlike the in-memory version, the data survives server restarts.

## Database

The database is stored in:

`tasks.db`

The file is automatically created when the application starts.

The database contains a `tasks` table with:

- `id` - Primary key
- `title` - Task title
- `done` - Completion status stored as 0 or 1

Three example tasks are automatically inserted only when the database is empty.

`tasks.db` is included in `.gitignore`, so a fresh clone creates its own database.

## How to Run

Install the dependencies:

```bash
pip install -r requirements.txt

Start the server:

python -m uvicorn main:app --reload

Open Swagger UI:

http://localhost:8000/docs

API Endpoints
Method	Endpoint	Description
GET	/	Welcome message
GET	/health	Health check
GET	/tasks	Get all tasks
GET	/tasks/{task_id}	Get one task
POST	/tasks	Create a task
PUT	/tasks/{task_id}	Update a task
DELETE	/tasks/{task_id}	Delete a task
Example SQL Query
SELECT * FROM tasks WHERE done = 1;

This returns all completed tasks.

Database Browser

The SQLite database was inspected using DB Browser for SQLite.

<img width="1600" height="854" alt="image" src="https://github.com/user-attachments/assets/6f52d857-813f-4093-abd3-e29ca02260b4" />


Persistence

Tasks are stored in SQLite instead of an in-memory Python list. Therefore, tasks remain available after restarting the FastAPI server.


<img width="957" height="1028" alt="image" src="https://github.com/user-attachments/assets/2b93fb84-0e3c-4edb-99c6-3294c7d7d64f" />

