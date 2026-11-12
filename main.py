
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthWeakPasswordError,
)

from database import get_db
from supabase_client import supabase

app = FastAPI()
bearer_scheme = HTTPBearer(
    scheme_name="SupabaseAccessToken",
    bearerFormat="JWT",
    description="Use the access_token returned by /auth/login.",
    auto_error=False,
)


class AuthenticationError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


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


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(
    request: Request,
    exc: AuthenticationError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
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


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None or not credentials.credentials:
        raise AuthenticationError(401, "Access token required")

    try:
        user_response = supabase.auth.get_user(credentials.credentials)
    except (AuthApiError, AuthInvalidJwtError) as exc:
        if isinstance(exc, AuthApiError) and (exc.status >= 500 or exc.status == 429):
            raise AuthenticationError(
                503,
                "Authentication service unavailable",
            ) from exc
        raise AuthenticationError(401, "Invalid or expired token") from exc
    except AuthRetryableError as exc:
        raise AuthenticationError(
            503,
            "Authentication service unavailable",
        ) from exc

    user = user_response.user if user_response else None
    if user is None:
        raise AuthenticationError(401, "Invalid or expired token")

    return user


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
def protected_profile(user=Depends(get_authenticated_user)):
    return _safe_user_info(user)


@app.get("/protected/dashboard")
def protected_dashboard(user=Depends(get_authenticated_user)):
    return {
        "message": "Welcome to your dashboard.",
        "user": _safe_user_info(user),
    }


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


@app.post("/auth/logout", status_code=204)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user=Depends(get_authenticated_user),
):
    try:
        supabase.auth.admin.sign_out(credentials.credentials, scope="global")
    except (AuthApiError, AuthInvalidJwtError) as exc:
        status_code = exc.status if isinstance(exc, AuthApiError) else 502
        raise AuthenticationError(
            status_code,
            "Logout failed",
        ) from exc
    except AuthRetryableError as exc:
        raise AuthenticationError(503, "Authentication service unavailable") from exc

    return Response(status_code=204)


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
