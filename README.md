# BEVoBIZ

Multi-tenant inventory + sales management SaaS. See `CLAUDE.md` for the
project summary, hard rules, and phase plan.

## Phase 1 — run order

Run these steps in order from the `BEVoBIZ` project root.

### 1. Start Postgres (with pgvector)

```bash
docker compose up -d
```

This starts Postgres 16 with the pgvector extension on `localhost:5432`
(credentials come from the root `.env` — copy `.env.example` if you
don't have one yet).

### 2. Configure and run the backend

```bash
cd backend
cp .env.example .env   # edit JWT_SECRET etc. if needed
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`. Swagger docs at
`http://localhost:8000/docs`.

### 3. Configure and run the frontend

In a new terminal:

```bash
cd frontend
cp .env.example .env   # defaults to http://localhost:8000
npm install
npm run dev
```

The app is now running at `http://localhost:5173`.

### 4. Try it out

- Go to `http://localhost:5173/signup`, create a business + account.
- You're redirected to the dashboard, showing "Welcome, {business name}".
- Refresh the page — you stay logged in.
- Click Logout — you're returned to the login page.

## Notes

- `backend/.env` and `frontend/.env` are gitignored — use the
  `.env.example` files as templates.
- Adding new tables later: create the SQLAlchemy model, import it in
  `backend/app/models/__init__.py`, then run
  `alembic revision --autogenerate -m "..."` followed by
  `alembic upgrade head`.
