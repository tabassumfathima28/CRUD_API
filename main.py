
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthInvalidCredentialsError,
    AuthRetryableError,
    AuthWeakPasswordError,
)

from database import get_db
from supabase_client import supabase

app = FastAPI()


# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()}
    )


# Request model
class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    done: bool = False


class AuthCredentials(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


def _safe_user_info(user):
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at,
    }


def _auth_response(auth_response):
    session = auth_response.session
    return {
        "user": _safe_user_info(auth_response.user),
        "access_token": session.access_token if session else None,
        "refresh_token": session.refresh_token if session else None,
    }


# Convert database row to dictionary
def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": row["done"]
    }


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/health")
def health_check():
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db": "ok"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


@app.get("/public/info")
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get("/protected/profile")
def protected_profile(authorization: str | None = Header(default=None)):
    parts = (authorization or "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JSONResponse(
            status_code=401,
            content={"error": "Access token required"},
        )

    try:
        user_response = supabase.auth.get_user(parts[1])
    except (AuthApiError, AuthInvalidJwtError) as exc:
        if isinstance(exc, AuthApiError) and (exc.status >= 500 or exc.status == 429):
            raise HTTPException(
                status_code=503,
                detail={"error": "Authentication service unavailable"},
            ) from exc
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )
    except AuthRetryableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "Authentication service unavailable"},
        ) from exc

    user = user_response.user if user_response else None
    if user is None:
        return JSONResponse(
            status_code=401,
            content={"error": "Invalid or expired token"},
        )

    return _safe_user_info(user)


@app.post("/auth/signup", status_code=201)
def signup(credentials: AuthCredentials):
    try:
        auth_response = supabase.auth.sign_up(
            {
                "email": credentials.email,
                "password": credentials.password,
            }
        )
    except (AuthApiError, AuthWeakPasswordError) as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": "Signup failed"},
        ) from exc
    except AuthRetryableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "Authentication service unavailable"},
        ) from exc

    return _auth_response(auth_response)


@app.post("/auth/login")
def login(credentials: AuthCredentials):
    try:
        auth_response = supabase.auth.sign_in_with_password(
            {
                "email": credentials.email,
                "password": credentials.password,
            }
        )
    except (AuthApiError, AuthInvalidCredentialsError) as exc:
        raise HTTPException(
            status_code=401,
            detail={"error": "Invalid email or password"},
        ) from exc
    except AuthRetryableError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "Authentication service unavailable"},
        ) from exc

    return _auth_response(auth_response)


# GET all tasks
@app.get("/tasks")
def get_tasks():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks ORDER BY id"
        ).fetchall()

    return [row_to_task(row) for row in rows]


# GET one task
@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = %s",
            (task_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return row_to_task(row)


# CREATE task
@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    with get_db() as conn:
        row = conn.execute(
            """
            INSERT INTO tasks (title, done)
            VALUES (%s, %s)
            RETURNING *
            """,
            (task.title, task.done)
        ).fetchone()

    return row_to_task(row)


# UPDATE task
@app.put("/tasks/{task_id}")
def update_task(task_id: int, task: TaskCreate):
    with get_db() as conn:
        row = conn.execute(
            """
            UPDATE tasks
            SET title = %s, done = %s
            WHERE id = %s
            RETURNING *
            """,
            (task.title, task.done, task_id)
        ).fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return row_to_task(row)


# DELETE task
@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = %s",
            (task_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Task not found"
            )

    return None
