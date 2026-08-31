# NCLEX Daily

NCLEX Daily is a mobile-first study application for short, motivating daily NCLEX practice. The repository currently contains **Phases 1–5**: foundation, authentication, a normalized private question bank, a secure backend quiz engine, and the complete responsive study experience.

## Architecture

- `frontend/`: React 18, Vite, TypeScript, React Router, TanStack Query, and Tailwind CSS
- `backend/`: Python 3.11+, FastAPI, Pydantic Settings, SQLAlchemy 2, Alembic, and PostgreSQL
- `docker-compose.yml`: local PostgreSQL 16 service

The frontend reads its API origin from `VITE_API_URL`. The backend exposes versioned routes under `/api/v1` and restricts browser origins with `CORS_ORIGINS`. Supabase manages credentials and browser sessions. FastAPI validates each bearer token with Supabase Auth before using the authenticated user's identity; frontend-provided user IDs are never trusted.

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker Desktop (for local PostgreSQL)

## First-time local setup

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

6. Validate and import the private question bank. The importer is transactional and
   safe to rerun: an invalid file is rejected without partial inserts, and existing
   questions are skipped by deterministic content hash.

   ```powershell
   python -m app.scripts.import_questions ..\data\original_nclex_study_question_bank_1700.csv
   python -m app.scripts.verify_question_bank --expect-child-topics 125
   ```

7. Start the backend:

   ```powershell
   uvicorn app.main:app --reload
   ```

8. In a second terminal, start the frontend:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

Open `http://localhost:5173`. The foundation screen should report that the API is connected. API documentation is available at `http://localhost:8000/docs`.

## Running the app after setup

Use three PowerShell terminals from the repository root.

Terminal 1 — start PostgreSQL:

```powershell
docker compose up -d postgres
```

Terminal 2 — apply pending migrations and start FastAPI:

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 3 — start React/Vite:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Stop either development server with `Ctrl+C`. Stop
PostgreSQL when you are finished with `docker compose stop postgres` from the
repository root.

### Testing from a phone on the same Wi-Fi

The Vite development server proxies `/api` to FastAPI, so the phone only needs to
reach port 5173. In `frontend/.env`, leave the local API value empty:

```env
VITE_API_URL=
```

Start FastAPI normally on `127.0.0.1:8000`, then expose only Vite to the local
network:

```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Find the computer's current Wi-Fi address with `ipconfig`, then open
`http://<computer-ip>:5173` on the phone. For example, this development machine
currently uses `http://192.168.1.175:5173`. Both devices must be on the same
non-guest Wi-Fi, and Windows Firewall must allow Node.js on Private networks.

Verify the same-origin API proxy from the phone at:

```text
http://<computer-ip>:5173/api/v1/health
```

For phone-based signup confirmation, add `http://<computer-ip>:5173/**` to
**Supabase → Authentication → URL Configuration → Redirect URLs**. The mobile UI
can be tested over local HTTP, but installing the PWA on a physical phone requires
HTTPS and is best tested from the deployed site.

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
- `VITE_ALLOW_SIGNUPS`: `false` for the invite-only private beta; `true` for local signup testing
- `VITE_SUPABASE_URL`: the same public Supabase project URL
- `VITE_SUPABASE_PUBLISHABLE_KEY`: the same low-privilege publishable key

No secrets belong in `VITE_*` variables. Vite embeds them into the browser bundle. This application does not need a Supabase secret key, legacy `service_role` key, or JWT signing secret for authentication. Never add those values to the frontend.

## Database migrations

Alembic is configured to read `DATABASE_URL` through the application settings. Once models are added, create and apply migrations from `backend/`:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Always run `alembic upgrade head` after pulling new code and before importing a
question bank. Alembic migrations change the database schema; importing or
activating a CSV changes question data and does not require a new migration. Do not
edit or delete an already-applied migration. If a future CSV introduces new fields
such as rationale or difficulty, update the model/importer and create a new
autogenerated migration before importing it.

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
   - Keep **Allow new users to sign up** enabled for local signup testing.
   - Disable it for the hosted private beta and invite testers from **Authentication → Users → Add User → Send invitation**. Do not create or share a temporary password.
   - For the production-like flow, keep **Confirm Email** enabled. You may disable it temporarily for faster local-only testing.
5. Open **Authentication → URL Configuration**:
   - Set **Site URL** to `http://localhost:5173` for local development.
   - Add `http://localhost:5173/**` to **Redirect URLs**.
   - When deployed, change Site URL to the production frontend URL and add the exact production callback pattern, for example `https://your-app.vercel.app/**`.
6. Put the project URL and publishable key in both `.env` files using the names in the examples. Both values are intentionally public; never substitute a secret key.
7. Keep the local Docker `DATABASE_URL` while developing. For Vercel, click **Connect**, choose the **Transaction pooler**, change its scheme to `postgresql+psycopg://`, and URL-encode special characters in the password. Use a direct connection for migrations when the local network supports IPv6; otherwise use the Session pooler for that one-time administration task.

Supabase hosted projects enable email confirmation by default. The built-in mailer is intended for testing and is rate limited; configure custom SMTP before production use.

### Authentication behavior

- Supabase JS persists and refreshes the browser session.
- After authentication, the app requests persistent browser storage and rechecks
  the saved session whenever an installed PWA resumes from the background.
- Invitation links open the app's `/set-password` flow. The tester chooses and
  confirms their own password before entering the protected application.
- `/dashboard` is protected and redirects anonymous visitors to `/login`.
- `/login` redirects authenticated visitors to `/dashboard`.
- The dashboard sends the Supabase access token as `Authorization: Bearer <token>` to `/api/v1/me`.
- FastAPI validates that token using Supabase Auth's `/auth/v1/user` endpoint and extracts the returned user identity.
- `/api/v1/me` creates the matching profile once. A unique database index plus conflict recovery makes simultaneous first requests idempotent.
- Backend timestamps use timezone-aware UTC values. Phase 4 streak calculations will use UTC calendar days unless a profile timezone is deliberately introduced.
- The migration enables PostgreSQL Row Level Security on `profiles` without browser Data API policies. Profile access intentionally goes through FastAPI only.

Calling Supabase Auth for token validation adds one regional network request to protected API calls, but it supports both current asymmetric signing keys and legacy HS256 projects without handling a signing secret. A later optimization can replace this service behind the same dependency with cached JWKS validation.

## Hosted private beta on Vercel

The beta uses one Vercel Services project connected to this private GitHub
repository:

- `frontend` is a Vite service mounted at `/`
- `backend` is a FastAPI service receiving `/api/*`
- Supabase continues to provide Auth and the production Postgres database

The root `vercel.json` defines both services and routes them through one domain.
The frontend therefore uses a same-origin API URL, avoiding a separate public API
hostname and cross-origin browser requests. The backend exports a recognized
FastAPI entrypoint in `backend/main.py`.

### 1. Prepare the production database

In Supabase, click **Connect** and copy two PostgreSQL connection strings:

- **Direct connection** for migrations/imports, or **Session pooler** if the local machine cannot use the IPv6 direct endpoint
- **Transaction pooler** for the Vercel backend runtime

For both URLs, replace the `postgresql://` or `postgres://` scheme with
`postgresql+psycopg://`, insert the database password, and URL-encode any special
characters in that password. Do not commit either URL.

From PowerShell, prepare the empty hosted database with the administration URL:

```powershell
cd backend
$env:DATABASE_URL = '<direct-or-session-pooler-sqlalchemy-url>'
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.scripts.import_question_json `
  ..\data\nclex_generated_3x_alternative_question_bank.json `
  --apply --activate
Remove-Item Env:DATABASE_URL
```

Run that import only against the intended hosted database. It is idempotent, but
the `--activate` option switches the active question set and abandons incomplete
sessions from any previous bank.

### 2. Create the Vercel Services project

1. In Vercel, select **Add New → Project** and import the private
   `Ryan31704/nclex-daily` GitHub repository.
2. Name it `nclex-daily`, leave **Root Directory** at the repository root, and
   select the **Services** application preset. Vercel will read the root
   `vercel.json` and detect the Vite and FastAPI services.
3. Leave build/output commands on their automatic defaults.
4. Add these **Production, Preview, and Development** environment variables:

   ```text
   APP_NAME=NCLEX Daily API
   APP_ENV=production
   LOG_LEVEL=INFO
   DATABASE_URL=<Supabase Transaction pooler URL using postgresql+psycopg://>
   DATABASE_SERVERLESS=true
   CORS_ORIGINS=https://<project>.vercel.app
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
   VITE_API_URL=
   VITE_ALLOW_SIGNUPS=false
   VITE_SUPABASE_URL=https://<project-ref>.supabase.co
   VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
   ```

5. Deploy and verify `https://<project>.vercel.app/api/v1/health` returns JSON
   with `status: ok`. An unauthenticated request to `/api/v1/me` must return `401`.

### 3. Lock the beta to invited testers

1. In **Supabase → Authentication → URL Configuration**, set **Site URL** to the
   production frontend URL and add `https://<frontend-project>.vercel.app/**` to
   **Redirect URLs**. Keep the localhost redirect for development.
2. In the Email provider settings, disable **Allow new users to sign up**.
3. Add each tester through **Authentication → Users → Add User → Send invitation**.
   The tester must open the link in that email instead of attempting to log in
   immediately. The link signs them in once, sends them to **Create your password**,
   and then opens the dashboard after the password is saved.
4. Keep `VITE_ALLOW_SIGNUPS=false`. This removes account creation from the app,
   while the Supabase setting is the server-enforced signup block.
5. Optionally enable Vercel Authentication for preview deployments. The production
   beta itself is gated by Supabase login so invited testers do not need Vercel
   accounts.

### 4. Release and rollback

Every push to `main` triggers CI plus one atomic Services deployment.
Use a Vercel preview deployment first for meaningful changes, complete the beta
checklist below, and only then promote it to production. Vercel retains earlier
deployments for rollback. Database migrations are a separate, explicit release
step and must be applied before code that depends on them.

Private-beta checklist:

1. Open the production URL in a private browser window; confirm account creation
   is absent and `/dashboard` redirects to `/login`.
2. Send an invitation to a test email and follow its link. Confirm the app asks
   the tester to create and confirm a password before showing the dashboard.
3. Log out, log back in with the new password, refresh `/dashboard`, and confirm
   the session persists.
4. Complete one practice question and one 10-question Quick Review; confirm answer
   feedback, progress, and XP persist after refresh.
5. Start a Random Test and confirm the requested question count loads.
6. Confirm `/api/v1/me` returns `200` with the browser's access token and `401`
   without it.
7. Log out and confirm protected pages return to `/login`.
8. Install the PWA from the HTTPS production URL on a phone and repeat login plus
   one practice question on cellular data.

## Question bank import

The currently active bank is the generated JSON set preserved at
`data/nclex_generated_3x_alternative_question_bank.json`: 3,732 questions across 413
leaf topics. It contains standard multiple choice plus multiple response,
numeric response, ordered response, highlight, cloze, matching, matrix, and
bow-tie questions. The app stores structured answer keys only in the backend and
sends clients a sanitized interaction definition with all correctness fields
removed.

The original private source is preserved at `data/original_nclex_study_question_bank_1700.csv`. The importer validates every required field, the `A - answer text` through `D - answer text` answer format, and an exact match between the answer text and its referenced choice. Invalid input is rejected before database changes and produces a CSV error report with the source row, error type, question text, and reason.

The source generates a two-level hierarchy: `chapter` values are parent topics and `topic` values are child topics. Each question is assigned to a child topic, has four ordered choices and one correct choice, and receives a deterministic unique content hash. Re-running the importer skips existing questions instead of duplicating them.

The supplied source contains 17 unique chapters and 125 unique chapter/topic pairs. This differs from the preliminary specification's estimate of 133 child topics; no topics are invented or hard-coded to mask that source-data discrepancy.

### Required CSV format

Every replacement or supplemental CSV must use these exact headers:

```text
question,answer,choice_a,choice_b,choice_c,choice_d,chapter,topic
```

Each row must contain all eight values. `answer` must use `A - answer text` through
`D - answer text`, and its answer text must exactly match the referenced choice
after trimming whitespace. Use a new descriptive filename for every generated
bank, such as `nclex_question_bank_2026_09.csv`; never overwrite the preserved
original file. Only import content you own or have permission to distribute.

### Importing additional questions

This keeps the current bank active and adds new unique questions.

1. Copy the new CSV into `data/`.
2. From `backend/`, apply migrations and import it:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   .\.venv\Scripts\python.exe -m app.scripts.import_questions ..\data\nclex_question_bank_2026_09.csv
   ```

3. Review the printed inserted/skipped counts. If validation fails, open the
   generated `.errors.csv`, correct every reported row, and rerun the importer.
4. Verify the cumulative stored bank using its expected totals. Because the current
   importer creates four choices per question, `expected choices = expected
   questions × 4`.

   ```powershell
   .\.venv\Scripts\python.exe -m app.scripts.verify_question_bank `
     --expect-questions 2000 `
     --expect-choices 8000 `
     --expect-parent-topics 17 `
     --expect-child-topics 125
   ```

Adjust all expected values to match the new cumulative dataset. Re-importing the
same file is idempotent and should report every question as skipped.

### Validating and replacing the bank from generated JSON

The JSON importer is the preferred path for a rich generated bank. It validates
unique IDs, required content, topics, supported question types, option references,
numeric answers, ordered answers, structured answer keys, and a maximum of 20
top-level choices before opening a database transaction.

First run a read-only validation from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.import_question_json `
  ..\data\nclex_generated_3x_alternative_question_bank.json
```

After backing up the database, import it and make it the only active bank:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.scripts.import_question_json `
  ..\data\nclex_generated_3x_alternative_question_bank.json `
  --apply --activate
```

The operation is idempotent: rerunning the same file skips existing rows. With
`--activate`, it verifies that every source question exists before switching the
active set, deactivates previous questions/topics, and abandons in-progress
sessions so they cannot retain questions from the former bank. Completed
sessions, attempts, XP, and progress history are preserved.

Generated stems are normalized during JSON import so repeated wrappers such as
`Clinical summary:`, `Handoff note:`, `Preceptor case:`, and generic planning
introductions are not shown to learners. To clean an already-imported active
bank, preview and then apply the same normalization:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.normalize_question_stems
.\.venv\Scripts\python.exe -m app.scripts.normalize_question_stems --apply
```

### Switching completely to a new active question set

Do not delete questions, choices, sessions, attempts, or progress rows. The
activation command preserves that history and changes only which questions and
topics are available for new practice sessions.

1. Back up the local database from the repository root:

   ```powershell
   New-Item -ItemType Directory -Force backups
   docker compose exec -T postgres pg_dump -U nclex -d nclex_daily > backups\nclex_daily_before_question_switch.sql
   ```

2. Change to `backend/`, then import and verify the new CSV as described above:

   ```powershell
   cd backend
   ```

3. Preview the exact activation plan. Preview mode never changes the database:

   ```powershell
   .\.venv\Scripts\python.exe -m app.scripts.activate_question_bank ..\data\nclex_question_bank_2026_09.csv
   ```

4. Confirm that `Questions matched in database` equals `Unique questions in
   requested set`. The command refuses to continue if any CSV question has not
   already been imported.
5. Activate the new set:

   ```powershell
   .\.venv\Scripts\python.exe -m app.scripts.activate_question_bank ..\data\nclex_question_bank_2026_09.csv --apply
   ```

6. Restart the backend and frontend, open `/progress`, and start a Random Test to
   confirm only the intended topics and questions are available.

The switch is reversible. To restore the original 1,700-question set, preview and
then apply the preserved original CSV:

```powershell
.\.venv\Scripts\python.exe -m app.scripts.activate_question_bank ..\data\original_nclex_study_question_bank_1700.csv
.\.venv\Scripts\python.exe -m app.scripts.activate_question_bank ..\data\original_nclex_study_question_bank_1700.csv --apply
```

Activation never deletes historical records. Existing completed sessions and
attempts remain available, while new Daily Practice, Quick Review, Random Test,
topic counts, and mastery coverage use only the active set.

Authenticated API routes:

- `GET /api/v1/topics`: hierarchical topic list with question counts
- `GET /api/v1/topics/{topic_id}`: topic detail and hierarchy context
- `GET /api/v1/questions/{question_id}`: development-only review response; choice correctness is intentionally excluded

## Quiz engine

Phase 4 adds append-only attempts, ordered session membership, daily and topic practice sessions, and per-user topic progress. Correctness, XP, mastery, streaks, and resource ownership are calculated and enforced in FastAPI; the client supplies only its response, while the answer key remains server-side.

Practice endpoints:

- `POST /api/v1/practice/daily/start`
- `POST /api/v1/practice/topic/{topic_id}/start`
- `POST /api/v1/practice/quick-review/start`
- `POST /api/v1/practice/random/start`
- `POST /api/v1/practice/review/{question_id}/start`
- `GET /api/v1/practice/sessions/{session_id}`
- `POST /api/v1/practice/sessions/{session_id}/answer`
- `POST /api/v1/practice/sessions/{session_id}/complete`
- `GET /api/v1/topics/{topic_id}/progress`
- `GET /api/v1/progress`
- `GET /api/v1/review/missed`
- `GET /api/v1/dashboard`

Daily sessions target 10 questions and approximate a 50% weak, 30% developing, and 20% strong/unseen topic mix, with unseen and previously missed questions preferred. Correct answers earn 10 XP, incorrect answers earn 5 XP, and completion of a daily session adds 25 XP. Duplicate answer submissions and repeated completion calls cannot award XP twice.

After the daily session, students can start unlimited **Quick Review** sessions containing another adaptive set of 10 questions. **Random Test** creates a fresh mixed test with 10, 20, 30, or 50 non-duplicated questions. These optional sessions award answer XP but do not add another daily completion bonus or increase the streak.

Mastery measures correct coverage of the full active question pool for each child topic. Each unique question contributes at most one point based on its latest answer, so unseen questions count as zero and repeats cannot inflate mastery. A later incorrect answer removes that question's point. Classifications are weak (0–39), developing (40–69), strong (70–99), and mastered only at 100%.

Streaks use UTC calendar dates consistently. Completing the first daily session on a UTC date records activity; repeated completions that day do not increase the streak again. Topic-only sessions do not count toward the daily streak.

## Frontend experience

Phase 5 adds an authenticated application shell with a desktop sidebar and mobile bottom navigation. Page routes are lazy-loaded so the login bundle does not include the complete study application.

Protected routes:

- `/dashboard`: greeting, streak/XP/attempt/mastery statistics, daily session CTA, weakest topics, and category progress
- `/progress`: complete NCLEX category roadmap with unique-question coverage mastery
- `/topics/:slug`: category or subtopic detail with practice actions
- `/practice`: daily or category practice selection
- `/practice/:sessionId`: one-question-at-a-time answer flow with server-confirmed feedback
- `/practice/:sessionId/complete`: score, XP, streak, and next actions
- `/review`: topic-filtered missed questions with exact-question retry
- `/profile`: account details, study totals, and logout

The practice interface never receives correct-choice flags before submission. It locks all choices after an answer, displays the correct answer and rationale returned by the server, and refreshes dashboard/progress/review caches after completion. After feedback, the Continue/Finish action stays pinned to the bottom of the viewport so answering never requires scrolling to find the next action. Imported questions without reviewed rationales show a clear content-review placeholder.

### Mobile and PWA

The frontend is an installable progressive web app. Production builds generate a web manifest and service worker, precache the application shell, provide standard and maskable icons, and prompt users when an updated version is ready. Network-dependent study actions show a clear offline message instead of silently failing.

- Android/desktop Chrome: use the in-app **Install app** prompt or the browser install button.
- iPhone/iPad Safari: tap **Share**, then **Add to Home Screen**.
- On iPhone/iPad, Safari and the installed Home Screen app keep separate website
  data. Complete the invitation, open the installed app, and log in there once.
  Subsequent launches should restore that installed app's saved session.
- The standalone layout respects notches and home indicators, uses a thumb-friendly bottom navigation, maintains 44px-or-larger controls, and has no horizontal overflow down to 320px.

The cached shell can launch offline, but authentication refreshes, loading questions, submitting answers, and synchronizing progress still require an internet connection.

## Current MVP limitations

Phase 5 includes the responsive dashboard, progress, topic, practice, answer-feedback, completion, review, and profile interfaces. The repository is configured for an invite-only Vercel beta. Rationales, difficulty review, clinical accuracy review, and distribution rights for the imported private bank remain content tasks and still block a public launch.

## Phase 2 manual test checklist

1. Visit `/login`, switch to **Create Account**, and submit a display name, email, and password.
2. If email confirmation is enabled, open the confirmation email and follow its link; then log in.
3. Confirm `/dashboard` shows the display name and email returned by `/api/v1/me`.
4. Refresh `/dashboard` and confirm it remains visible without briefly showing `/login`.
5. While logged in, visit `/login` and confirm it redirects to `/dashboard`.
6. Select **Log Out** and confirm the app returns to `/login`.
7. While logged out, visit `/dashboard` directly and confirm it redirects to `/login`.
8. In browser developer tools, call or inspect `GET http://localhost:8000/api/v1/me` with no bearer token and confirm it returns `401`; the dashboard's authenticated request should return `200`.

## Private-beta invitation test checklist

1. Keep public signups disabled in both Supabase and `VITE_ALLOW_SIGNUPS`.
2. In **Supabase → Authentication → Users**, select **Add user → Send invitation**
   and enter a fresh test email address.
3. Confirm entering that email directly on `/login` does not grant access before
   the invitation is accepted.
4. Open the invitation email and follow its link. The app must show
   **Create your password**, not the dashboard or login error.
5. Try mismatched passwords and a password shorter than eight characters; confirm
   both are rejected with a useful message.
6. Save a valid password and confirm the dashboard opens.
7. Log out, then log in again using the invited email and newly created password.
8. Reopen the already-used invitation link and confirm it cannot create another
   account or bypass authentication.

## Content Licensing

Only original, user-owned, public-domain, or properly licensed question content should be distributed through this application. Commercial NCLEX prep questions and rationales must not be copied, lightly paraphrased, scraped, or imported without appropriate distribution rights.

The Phase 3 CSV is treated as private review material. Imported rows are marked `source_type=imported_private`, preserve the exact source filename, and use `license_status=review_required`; rationales and difficulty remain unset. Do not expose, redistribute, or deploy this content publicly until ownership and distribution rights are reviewed and recorded. The backend enables Row Level Security without direct browser policies, and question data is served only through authenticated FastAPI routes.
