# NCLEX Daily

NCLEX Daily is a mobile-first study application for short, motivating daily NCLEX practice. The repository currently contains **Phase 1: Foundation** and **Phase 2: Authentication**: a FastAPI API, PostgreSQL/SQLAlchemy/Alembic plumbing, Supabase email/password authentication, protected React routing, and automatic profile provisioning.

## Architecture

- `frontend/`: React 18, Vite, TypeScript, React Router, TanStack Query, and Tailwind CSS
- `backend/`: Python 3.11+, FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic, and PostgreSQL
- `docker-compose.yml`: local PostgreSQL 16 service

The frontend reads its API origin from `VITE_API_URL`. The backend exposes versioned routes under `/api/v1` and restricts browser origins with `CORS_ORIGINS`. Supabase manages credentials and browser sessions. FastAPI validates each bearer token with Supabase Auth before using the authenticated user's identity; frontend-provided user IDs are never trusted.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (for local PostgreSQL)

## Local installation

1. Copy the example environment files:

   ```powershell
   Copy-Item backend/.env.example backend/.env
   Copy-Item frontend/.env.example frontend/.env
   ```

2. Fill in the Supabase values described in [Supabase project setup](#supabase-project-setup).

3. Start PostgreSQL:

   ```powershell
   docker compose up -d postgres
   ```

4. Create the backend virtual environment and install dependencies:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

5. Apply database migrations:

   ```powershell
   alembic upgrade head
   ```

6. Start the backend:

   ```powershell
   uvicorn app.main:app --reload
   ```

7. In a second terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. The foundation screen should report that the API is connected. API documentation is available at `http://localhost:8000/docs`.

## Environment variables

Backend variables are documented in `backend/.env.example`:

- `DATABASE_URL`: SQLAlchemy PostgreSQL connection URL
- `CORS_ORIGINS`: comma-separated trusted frontend origins
- `APP_ENV`: environment label returned by the health check
- `LOG_LEVEL`: backend logging level
- `SUPABASE_URL`: public project URL, such as `https://abc.supabase.co`
- `SUPABASE_PUBLISHABLE_KEY`: the project's low-privilege `sb_publishable_...` key

Frontend variables are documented in `frontend/.env.example`:

- `VITE_API_URL`: public backend origin, without a trailing slash
- `VITE_SUPABASE_URL`: the same public Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY`: the same low-privilege publishable key

No secrets belong in `VITE_*` variables. Vite embeds them into the browser bundle. This application does not need a Supabase secret key, legacy `service_role` key, or JWT signing secret for authentication. Never add those values to the frontend.

## Database migrations

Alembic is configured to read `DATABASE_URL` through the application settings. Once models are added, create and apply migrations from `backend/`:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Tests and checks

```powershell
cd backend
pytest

cd ../frontend
npm run lint
npm run build
```

## Supabase project setup

1. Sign in to Supabase, select **New project**, choose an organization and nearby region, set a strong database password, and wait for provisioning to finish.
2. Open **Settings → API Keys**. If the project has no `sb_publishable_...` key, select **Create new API key**, choose **Publishable**, and copy it. Do not copy a secret or `service_role` key.
3. Obtain the project URL from the project's **Connect** dialog or **Integrations → Data API**. It has the form `https://<project-ref>.supabase.co`.
4. Open **Authentication → Sign In / Providers → Email**:
   - Enable the Email provider.
   - Keep **Allow new users to sign up** enabled.
   - For the production-like flow, keep **Confirm Email** enabled. You may disable it temporarily for faster local-only testing.
5. Open **Authentication → URL Configuration**:
   - Set **Site URL** to `http://localhost:5173` for local development.
   - Add `http://localhost:5173/**` to **Redirect URLs**.
   - When deployed, change Site URL to the production frontend URL and add the exact production callback pattern, for example `https://your-app.vercel.app/**`.
6. Put the project URL and publishable key in both `.env` files using the names in the examples. Both values are intentionally public; never substitute a secret key.
7. Keep the local Docker `DATABASE_URL` while developing, or click **Connect** in Supabase and copy the **Session pooler** connection string for a persistent Railway/Render backend. Change its scheme to `postgresql+psycopg://` and URL-encode special characters in the password.

Supabase hosted projects enable email confirmation by default. The built-in mailer is intended for testing and is rate limited; configure custom SMTP before production use.

### Authentication behavior

- Supabase JS persists and refreshes the browser session.
- `/dashboard` is protected and redirects anonymous visitors to `/login`.
- `/login` redirects authenticated visitors to `/dashboard`.
- The dashboard sends the Supabase access token as `Authorization: Bearer <token>` to `/api/v1/me`.
- FastAPI validates that token using Supabase Auth's `/auth/v1/user` endpoint and extracts the returned user identity.
- `/api/v1/me` creates the matching profile once. A unique database index plus conflict recovery makes simultaneous first requests idempotent.
- Backend timestamps use timezone-aware UTC values. Phase 4 streak calculations will use UTC calendar days unless a profile timezone is deliberately introduced.
- The migration enables PostgreSQL Row Level Security on `profiles` without browser Data API policies. Profile access intentionally goes through FastAPI only.

Calling Supabase Auth for token validation adds one regional network request to protected API calls, but it supports both current asymmetric signing keys and legacy HS256 projects without handling a signing secret. A later optimization can replace this service behind the same dependency with cached JWKS validation.

## Deployment direction

- Frontend: Vercel, with `VITE_API_URL` set to the deployed FastAPI origin.
- Backend: Railway or Render, with `DATABASE_URL`, `CORS_ORIGINS`, and later Supabase JWT verification variables configured as secrets.
- Database: Supabase Postgres in production.

Exact deployment and production-hardening instructions will be completed in Phase 6.

## Current MVP limitations

Phase 2 includes authentication and the Profile model. Topic/question models, seed data, question import, quiz behavior, progress tracking, and final production deployment configuration remain for Phases 3–6.

## Phase 2 manual test checklist

1. Visit `/login`, switch to **Create Account**, and submit a display name, email, and password.
2. If email confirmation is enabled, open the confirmation email and follow its link; then log in.
3. Confirm `/dashboard` shows the display name and email returned by `/api/v1/me`.
4. Refresh `/dashboard` and confirm it remains visible without briefly showing `/login`.
5. While logged in, visit `/login` and confirm it redirects to `/dashboard`.
6. Select **Log Out** and confirm the app returns to `/login`.
7. While logged out, visit `/dashboard` directly and confirm it redirects to `/login`.
8. In browser developer tools, call or inspect `GET http://localhost:8000/api/v1/me` with no bearer token and confirm it returns `401`; the dashboard's authenticated request should return `200`.

## Content Licensing

Only original, user-owned, public-domain, or properly licensed question content should be distributed through this application. Commercial NCLEX prep questions and rationales must not be copied, lightly paraphrased, scraped, or imported without appropriate distribution rights. Future question records and imports will include provenance and license metadata for auditability.
