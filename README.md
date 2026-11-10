# ProofPay AI

**Fair payments and AI-assisted verification for freelance work.**

ProofPay AI is a freelance workflow MVP built for the PayPal AI Hackathon. It helps clients and freelancers establish clear agreements, submit work, review AI-assisted verification, and complete payments through PayPal Sandbox.

## 🚀 Features

1. **Task Creation:** Create freelance tasks with an INR budget and deadline.
2. **AI Agreement Generation:** Generate structured freelance agreements using a locally hosted Ollama model.
3. **Agreement Approval:** Allow clients to review and confirm agreements.
4. **Work Submission:** Upload deliverables in PDF, PNG, and JPG formats.
5. **AI Work Verification:** Compare submitted work against agreed requirements using advisory AI verification.
6. **Client Review:** Clients can accept submitted work or request revisions.
7. **PayPal Sandbox Payments:** Create and capture a USD 1.00 technical test transaction after buyer approval.

### Important Payment and AI Limitations

- The original task budget is maintained in INR and is never converted or overwritten.
- The USD 1.00 PayPal transaction is a technical Sandbox test, not the actual INR task payment.
- Ordinary PayPal Checkout is not escrow.
- AI verification provides recommendations only. The client makes the final decision.
- Payment is marked complete only after the backend successfully captures an approved PayPal order. A browser redirect alone does not confirm payment.

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| Frontend | React, Vite, TypeScript |
| Styling | Tailwind CSS |
| Database | SQLite / PostgreSQL |
| AI | Ollama, Qwen3 1.7B |
| Payments | PayPal Sandbox |
| Testing | Pytest |

## 📁 Repository Structure

```text
proofpay-ai/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── .env.example
│   └── index.html
│
└── README.md
```

## ⚙️ Prerequisites

Install the following before running the project:

- Python 3.10 or later
- Node.js and npm
- Git
- PayPal Developer Sandbox account
- Ollama (optional, for AI features)

## 💻 Local Installation and Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/anubhavsingh23906-code/ProofPay-AI.git
cd ProofPay-AI
```

### 2. Backend Setup

Open PowerShell inside the `backend` directory:

```powershell
cd backend
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create the environment configuration:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and configure the required environment variables, including your PayPal Sandbox Client ID and Secret.

**Never upload your actual `.env` file or PayPal credentials to GitHub.**

Start the backend:

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend API:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### 3. Optional AI Setup (Ollama)

Install [Ollama](https://ollama.com/).

Download the model:

```powershell
ollama pull qwen3:1.7b
```

Keep Ollama running while using AI agreement generation and verification.

If Ollama is unavailable, basic task APIs remain usable, while AI-dependent operations return an error.

### 4. Frontend Setup

Open another PowerShell terminal and navigate to the frontend directory:

```powershell
cd frontend
```

Install dependencies:

```powershell
npm install
```

Create the environment configuration:

```powershell
Copy-Item .env.example .env
```

Start the development server:

```powershell
npm run dev
```

Open:

http://localhost:5173

The Vite development proxy forwards `/api` requests to the backend. Leave `VITE_API_URL` empty for local development unless your configuration requires otherwise.

## 🧪 Running Tests

From the backend directory, activate the virtual environment and execute:

```powershell
pytest -q
```

The automated tests cover:

- Task creation
- Payment gating
- Approval-link handling
- Capture-before-approval rejection
- Task matching
- Duplicate payment capture

**Note:** Tests mock PayPal interactions and do not create real payment transactions.

## 💳 PayPal Sandbox Payment Workflow

ProofPay AI uses PayPal Sandbox to demonstrate the payment lifecycle.

1. Client reviews and accepts submitted work.
2. Frontend requests a payment order through `POST /tasks/{id}/create-payment`.
3. Backend creates a PayPal Sandbox order.
4. Buyer approves the order through PayPal Sandbox.
5. PayPal redirects the buyer to `/payment/success?task_id=...&token=ORDER_ID`.
6. Frontend requests payment capture through `POST /tasks/{id}/capture-payment`.
7. Backend retrieves the PayPal order, verifies its association with the task, and checks its status.
8. The backend captures the order only when its status is `APPROVED`, or records it when already `COMPLETED`.

**Sandbox test amount:** USD 1.00

**Task budget:** INR, unchanged.

## 🗄️ Database Configuration

### Local Development

The default database is SQLite:

```text
backend/proofpay.db
```

Application startup uses SQLAlchemy `create_all` to create missing tables. It does not delete existing database rows.

### Production Database

For deployment, PostgreSQL is recommended.

A managed PostgreSQL provider such as [Neon](https://neon.com/) can be used.

Configure `DATABASE_URL`:

```text
postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
```

Do not rely on a disposable SQLite file on a hosting instance because its data may disappear after a restart.

Existing local SQLite records are not automatically migrated to PostgreSQL.

## 🌐 Deployment Instructions

The repository includes deployment instructions for Render and Vercel. Hosting projects and production secrets must be configured separately.

### Backend Deployment — Render

1. Create a new Web Service on [Render](https://render.com/).
2. Select this GitHub repository.
3. Set the root directory to `backend`.
4. Configure the build command:

```bash
pip install -r requirements.txt
```

5. Configure the start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

6. Configure the required environment variables.
7. Set `DATABASE_URL` to a managed PostgreSQL database URL.
8. Configure `FRONTEND_URL` and `CORS_ORIGINS` with your deployed frontend origin.

**AI hosting note:** Ollama is not expected to run on a typical free Render instance. AI-dependent features require a reachable Ollama host or a locally hosted demonstration.

### Frontend Deployment — Vercel

1. Create a project on [Vercel](https://vercel.com/).
2. Import this GitHub repository.
3. Set the root directory to `frontend`.
4. Configure the build command:

```bash
npm run build
```

5. Set the output directory:

```text
dist
```

6. Configure the environment variable:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
```

7. Deploy the frontend.

## 📡 Important API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health and Ollama status |
| GET | `/dashboard` | Task counters |
| POST | `/tasks` | Create a task |
| GET | `/tasks` | List tasks |
| GET | `/tasks/{id}` | Retrieve task details |
| POST | `/tasks/{id}/generate-agreement` | Generate AI agreement |
| POST | `/tasks/{id}/approve-agreement` | Approve or request agreement changes |
| POST | `/tasks/{id}/upload-files` | Upload work files |
| POST | `/tasks/{id}/submit-work` | Submit work description |
| POST | `/tasks/{id}/verify-work` | Run advisory AI verification |
| POST | `/tasks/{id}/review-verification` | Accept or request revision |
| POST | `/tasks/{id}/create-payment` | Create PayPal Sandbox order |
| POST | `/tasks/{id}/capture-payment` | Capture approved payment |
| GET | `/tasks/{id}/payment` | Retrieve payment status |

For complete request and response schemas, open the interactive API documentation at `/docs`.

## 🎯 Demo Workflow for Judges

To test the application locally:

1. Start the FastAPI backend.
2. Start the React frontend.
3. Ensure Ollama is running with `qwen3:1.7b` if testing AI features.
4. Create a freelance task with an INR budget.
5. Generate and review the AI agreement.
6. Confirm the agreement.
7. Upload and submit work.
8. Run AI verification.
9. Accept the work or request revisions as the client.
10. Test the PayPal Sandbox payment workflow using Sandbox credentials and a Sandbox buyer account.

## 🔐 Security Notes

- Never commit API secrets or `.env` files.
- Use PayPal Sandbox credentials for testing.
- Do not use live payment credentials in the hackathon demonstration.
- AI verification is advisory, not an automated payment authorization.
- Payment capture is validated by the backend against PayPal order information.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**Built for the PayPal AI Hackathon.**

