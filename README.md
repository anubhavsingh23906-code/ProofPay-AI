# ProofPay AI

ProofPay AI is a freelance workflow MVP for the PayPal AI Hackathon.

It helps a client and freelancer:

1. Create a task with an **INR** budget
2. Draft an agreement with a local Ollama model
3. Confirm that agreement
4. Upload work (PDF, PNG, JPG)
5. Run **advisory** AI verification
6. Let the **client** accept or request a revision
7. Start a **PayPal Sandbox** checkout for a **USD 1.00 technical test transaction**

The INR budget is never converted or overwritten. Ordinary PayPal Checkout is **not escrow**. AI recommendations are advisory; the client makes the final decision. Payment is marked complete only after the server captures an approved PayPal order — not because the browser landed on the success page.

## Repository layout

```
proofpay-ai/
  backend/     FastAPI API, SQLite/PostgreSQL, PayPal Sandbox
  frontend/    React + Vite + TypeScript + Tailwind
```

## Local setup

### 1. Backend

In PowerShell, from `proofpay-ai/backend`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and add your **PayPal Sandbox** client ID and secret. Do not put live PayPal credentials here.

Start the API (this serves the app on http://127.0.0.1:8000 and interactive docs on http://127.0.0.1:8000/docs):

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Optional AI: install [Ollama](https://ollama.com), then `ollama pull qwen3:1.7b` and keep Ollama running. If Ollama is down, task APIs still work; agreement generation and verification return a clear error.

### 2. Frontend

From `proofpay-ai/frontend`:

```powershell
npm install
copy .env.example .env
npm run dev
```

Open http://localhost:5173. In development the Vite proxy forwards `/api` to the backend, so you can leave `VITE_API_URL` empty locally.

### 3. Tests

From `proofpay-ai/backend` with the virtual environment active:

```powershell
pytest -q
```

These tests cover task creation, payment gating, approval-link handling, capture-before-approval rejection, task matching, and duplicate capture. They **mock** PayPal and do not create real charges.

## PayPal Sandbox flow

1. Client accepts work.
2. Frontend calls `POST /tasks/{id}/create-payment`.
3. Buyer approves the order on PayPal Sandbox.
4. PayPal returns to `/payment/success?task_id=...&token=ORDER_ID`.
5. Frontend calls `POST /tasks/{id}/capture-payment`.
6. Backend loads the order from PayPal, checks it belongs to that task, and captures only if status is `APPROVED` (or records it if already `COMPLETED`).

Test amount: **USD 1.00**. Task budget: **INR**, unchanged.

## Production database

Local default: SQLite file `backend/proofpay.db`. Starting the app calls `create_all`, which **adds missing tables only** and does not delete existing rows.

For Render, set `DATABASE_URL` to a managed PostgreSQL URL (Neon is a good option):

```
postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
```

Do not point production at a disposable SQLite file on the web server — that file disappears when the instance restarts.

Existing local SQLite data is not migrated automatically to Neon. If you need to copy local tasks into Postgres, ask before any destructive change.

## Deploy (when you are ready)

This repo is **deployment-ready**. It is not deployed until you create the hosting projects and set secrets.

### Backend on Render

1. Create a Web Service with root directory `proofpay-ai/backend` (or this `backend` folder if that is the Render root).
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Set env vars from `.env.example`, using a PostgreSQL `DATABASE_URL`.
5. Set `FRONTEND_URL` to the Vercel URL and `CORS_ORIGINS` to the same origin.

Ollama will not run on a typical free Render instance. Agreement generation then needs a reachable Ollama host, or you demo that part locally.

### Frontend on Vercel

1. Root directory: `proofpay-ai/frontend`
2. Build command: `npm run build`
3. Output directory: `dist`
4. Env: `VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com`

## Important API routes

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Health, including whether Ollama is reachable |
| GET | `/dashboard` | Task counters |
| POST | `/tasks` | Create task |
| GET | `/tasks` | List tasks |
| GET | `/tasks/{id}` | Full task, agreement, verification, payment |
| POST | `/tasks/{id}/generate-agreement` | AI draft agreement |
| POST | `/tasks/{id}/approve-agreement` | Client confirms or requests changes |
| POST | `/tasks/{id}/upload-files` | Upload PDF/PNG/JPG |
| POST | `/tasks/{id}/submit-work` | Submit work description |
| POST | `/tasks/{id}/verify-work` | Advisory AI verification |
| POST | `/tasks/{id}/review-verification` | Client accept / revision |
| POST | `/tasks/{id}/create-payment` | Create Sandbox order |
| POST | `/tasks/{id}/capture-payment` | Capture after buyer approval |
| GET | `/tasks/{id}/payment` | Payment status from DB and PayPal |

Interactive docs: `/docs`.
