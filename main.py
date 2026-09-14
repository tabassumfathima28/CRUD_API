from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import sqlite3

app = FastAPI()


# -------------------------
# Database setup
# -------------------------

def get_db():
    conn = sqlite3.connect("tasks.db")
    conn.row_factory = sqlite3.Row
    return conn


# Create database and table
conn = get_db()

conn.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
    )
""")

conn.commit()


# Seed 3 tasks only if database is empty
cursor = conn.execute("SELECT COUNT(*) FROM tasks")
count = cursor.fetchone()[0]

if count == 0:
    seed_tasks = [
        ("Learn FastAPI", 0),
        ("Learn SQLite", 0),
        ("Finish A2", 0)
    ]

    conn.executemany(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        seed_tasks
    )

    conn.commit()

conn.close()


# -------------------------
# Error handling
# -------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )


# -------------------------
# Models
# -------------------------

class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    done: bool = False


# -------------------------
# Helper
# -------------------------

def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"])
    }


# -------------------------
# Basic endpoints
# -------------------------

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# -------------------------
# GET all tasks
# -------------------------

@app.get("/tasks")
def get_tasks():
    conn = get_db()

    rows = conn.execute(
        "SELECT * FROM tasks"
    ).fetchall()

    conn.close()

    return [row_to_task(row) for row in rows]


# -------------------------
# GET one task
# -------------------------

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    conn = get_db()

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return row_to_task(row)


# -------------------------
# CREATE task
# -------------------------

@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    conn = get_db()

    cursor = conn.execute(
        "INSERT INTO tasks (title, done) VALUES (?, ?)",
        (task.title, int(task.done))
    )

    conn.commit()

    task_id = cursor.lastrowid

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return row_to_task(row)


# -------------------------
# UPDATE task
# -------------------------

@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskCreate):
    conn = get_db()

    cursor = conn.execute(
        """
        UPDATE tasks
        SET title = ?, done = ?
        WHERE id = ?
        """,
        (task.title, int(task.done), task_id)
    )

    conn.commit()

    if cursor.rowcount == 0:
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,)
    ).fetchone()

    conn.close()

    return row_to_task(row)


# -------------------------
# DELETE task
# -------------------------

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    conn = get_db()

    cursor = conn.execute(
        "DELETE FROM tasks WHERE id = ?",
        (task_id,)
    )

    conn.commit()

    conn.close()

    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return