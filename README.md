# CRUD API with Supabase Authentication

A FastAPI backend that combines the A3 PostgreSQL task CRUD API with Supabase
Auth signup, login, JWT verification, protected endpoints, and logout.

## Technologies

- Python 3.14
- FastAPI and Uvicorn
- Supabase Auth Python SDK
- PostgreSQL and psycopg
- Docker Compose

## Authentication

Signup and login use Supabase Auth. Login returns a Supabase `access_token` and
`refresh_token`. Protected requests send the access token as a Bearer token.
The API verifies it with Supabase Auth's `get_user(token)` and uses the returned
user record; it does not trust or decode an unverified JWT. Profile responses
contain only the user's ID, email, and account creation date.

Logout requires a verified Bearer token and revokes the current Supabase
session using that token. Supabase access tokens remain usable until their
expiration, so clients should discard the token after logout.

## Setup and run

1. Copy `.env.example` to `.env`.
2. Set `POSTGRES_PASSWORD`, `SUPABASE_URL`, and `SUPABASE_KEY`. Use a Supabase
   anon/public or publishable key only; never use a `service_role` or secret
   key. Keep `.env` private and out of Git.
3. Build and start the API and PostgreSQL with one command:

   ```bash
   docker compose up --build
   ```

The API is available at `http://localhost:8000`; PostgreSQL data persists in
the `taskdata` Docker volume. Stop the services with `docker compose down`.

## API reference

| Method | Endpoint | Authentication | Success | Description |
|---|---|---|---|---|
| POST | `/auth/signup` | No | 201 | Create a Supabase Auth user |
| POST | `/auth/login` | No | 200 | Sign in and return access/refresh tokens |
| POST | `/auth/logout` | Bearer token | 204 | Revoke the verified Supabase session |
| GET | `/public/info` | No | 200 | Public welcome information |
| GET | `/protected/profile` | Bearer token | 200 | Return safe authenticated-user information |
| GET | `/protected/dashboard` | Bearer token | 200 | Protected dashboard response |
| GET | `/` | No | 200 | Root welcome message |
| GET | `/health` | No | 200 | Check API and database availability |
| GET | `/tasks` | No | 200 | List tasks |
| GET | `/tasks/{task_id}` | No | 200 | Read a task; 404 if missing |
| POST | `/tasks` | No | 201 | Create a task; 400 for invalid input |
| PUT | `/tasks/{task_id}` | No | 200 | Update a task; 404 if missing |
| DELETE | `/tasks/{task_id}` | No | 204 | Delete a task; 404 if missing |

Auth requests with missing fields return 400. Invalid login credentials and
missing/invalid protected-route tokens return 401. The protected routes return
401 with `{"error":"Access token required"}` when credentials are missing or
malformed and `{"error":"Invalid or expired token"}` when Supabase rejects the
token.

## Example requests

Signup:

```bash
curl -i -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"choose-a-password"}'
```

Login (use the returned `access_token` and `refresh_token`):

```bash
curl -i -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"choose-a-password"}'
```

Public information:

```bash
curl -i http://localhost:8000/public/info
```

Protected profile and dashboard:

```bash
curl -i http://localhost:8000/protected/profile \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
curl -i http://localhost:8000/protected/dashboard \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Logout:

```bash
curl -i -X POST http://localhost:8000/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

## Swagger UI

Open [http://localhost:8000/docs](http://localhost:8000/docs). Select
**Authorize**, paste the access token returned by `/auth/login` (without the
`Bearer ` prefix), and confirm. Protected endpoints display a lock and
**Try it out** will send the Bearer token automatically.

![Swagger UI showing Bearer authentication](swagger.png)

## Existing task API

The task API uses `DATABASE_URL`; in Docker Compose the API connects to the
PostgreSQL service over the Compose network. On startup the application creates
the `tasks` table if needed and seeds three tasks only when the table is empty.
