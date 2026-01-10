# Repository Structure & File Roles

## Top Level Overview
- `app/`: FastAPI backend containing agents, APIs, core utilities (auth, blog, posts), SQLAlchemy models, and schema definitions.
- `frontend/`: Next.js app with login, blog management, and status dashboards under `src/app`, plus shared config (`next.config.ts`, `tsconfig.json`, etc.).
- `database/`: SQL script templates (currently `schema.sql`).
- `scripts/`: Utility cron jobs (`cron.py` for scheduled tasks).
- `geminilist.py`: CLI helper to list available Gemini models via the `google-genai` SDK.
- `requirements.txt` / `README.md`: Python deps and project overview.

## Backend Breakdown (`app/`)
- `agents/`: Capsule components orchestrating Gemini calls (`KnowledgeAgent`, `WriterAgent`, `SEOAgent`, `PublisherAgent`) used by workflow API.
- `models/sql_models.py`: SQLAlchemy ORM with `User`, `Blog`, `Post`, and relationships; now includes credits, alias, view_count, keyword_ranks for multi-blog tracking.
- `schemas.py`: Pydantic models for users, tokens, blogs, post statuses used by all API endpoints.
- `core/`:
  - `database.py`: Engine/session setup plus `init_db()` for SQLite.
  - `security.py`: Hashing, JWT creation, secret loaded from `.env`.
  - `deps.py`: `OAuth2PasswordBearer` dependency that validates bearer tokens and loads the current user.
  - `config.py`: Central settings (environment loading, secrets).
- `api/v1/`: Feature APIs:
  - `auth.py`: `signup`/`login` handling password hashing and JWT issuance.
  - `blogs.py`: Blog registration/listing, supports unlimited blogs per user and API token storage.
  - `posts.py`: `GET /status` returning per-blog post metrics for the dashboard via `PostStatusResponse`.
  - other placeholder modules (`admin.py`, `dashboard.py`) for future features.
- `main.py`: FastAPI app creation, CORS middleware, DB initialization, and router inclusion (`auth`, `blogs`, `posts` plus AI workflow endpoint).
- `services/`: Supporting utilities such as crawlers and indexing helpers.

## Frontend Breakdown (`frontend/src/app/`)
- `login/page.tsx`: Client-side authentication form storing JWT and switching between login/register with validations.
- `(user)/blogs/page.tsx`: Blog management interface fetching `/api/v1/blogs`, showing cards, and allowing additions with platform and alias data.
- `(user)/status/page.tsx`: Publication dashboard calling `/api/v1/posts/status` to display titles, timestamps, views, keyword ranks, and status badges.
- `(user)/dashboard/page.tsx`: (Existing admin view) Entry point to user workspace; may host aggregated controls in future.
- `page.tsx`: Landing page with marketing hero, feature blurb, and CTA buttons.
- `layout.tsx` / `globals.css`: Shared layout and styling for Next.js app.

## Scripts & Tools
- `geminilist.py`: Utility to enumerate Gemini models using `google-genai`; loads `.env` and prints `genai.models.list()` results.
- `scripts/cron.py`: Scheduled job runner (details TBD).

## Environment & Dependencies
- `requirements.txt` now references `pydantic[email]`, `google-genai`, `email-validator`, and all backend deps.
- `frontend/package.json` governs the Next.js app; install via `npm install` and run `npm run dev`.
- `.env` (not committed) should define `GEMINI_API_KEY`, `SECRET_KEY`, and database credentials when switching from SQLite.

## Recommended Workflow
1. Rebuild the DB: delete `sql_app.db` and restart FastAPI (`uvicorn app.main:app --reload`) so new columns take effect.
2. Start Next.js: `cd frontend && npm install && npm run dev`.
3. Use `/login` to get a JWT, add blogs via `/blogs`, and monitor publishing in `/status`.

