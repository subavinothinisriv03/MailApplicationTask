# AI Mail App — Autonomous UI-Controlling Email Web Application

> A production-ready email application where an AI assistant actively controls the user interface through natural language commands (progressive form typing, page navigation, email filtering, reading, replying, and sending with safety confirmation guards).

---

## 🏗️ Architecture Overview

The system follows a reactive, tool-driven event loop that translates natural language intent directly into user interface state transitions:

```text
User Command ("Compose to John...")
  ↓
Assistant Sidebar (Client UI)
  ↓
POST /api/assistant/chat (Context: current view, opened email, filters, draft state)
  ↓
OpenAI Tool Calling (or Local Fallback Parser)
  ↓
Backend Tool Execution (Database & Gmail API)
  ↓
WebSocket Broadcast (/ws)
  ↓
Frontend WebSocket Client (lib/websocket.ts)
  ↓
Zustand Stores (emailStore, uiStore, assistantStore)
  ↓
React UI (Field-by-field typing animation, page navigation, active filters)
```

---

## 🚀 Quick Start (Windows)

Simply double-click:
```bat
start.bat
```
This script automatically checks virtual environments, installs dependencies if missing, and launches both the **FastAPI Backend (port 8000)** and **Next.js Frontend (port 3000)**.

---

## 📋 Prerequisites
- **Node.js**: v18+ (tested on v24)
- **Python**: 3.10+ (tested on 3.12)
- **Package Managers**: `npm` and `pip` (or `uv`)

---

## ⚙️ Manual Setup & Installation

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# Windows (PowerShell / Command Prompt)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
```

**Run Backend:**
```bash
uvicorn app.main:app --reload --port 8000
```
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Run Next.js in development mode
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🔐 Configuration & Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Default |
| :--- | :--- | :--- |
| `APP_NAME` | Application Name | `AI Mail App` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DATABASE_URL` | SQLAlchemy Database URI | `sqlite:///./mail.db` |
| `FRONTEND_URL` | Frontend URL for CORS & redirects | `http://localhost:3000` |
| `BACKEND_URL` | Backend public URL | `http://localhost:8000` |
| `GOOGLE_CLIENT_ID` | Google Cloud OAuth Client ID | *(optional for demo)* |
| `GOOGLE_CLIENT_SECRET`| Google Cloud OAuth Client Secret | *(optional for demo)* |
| `GOOGLE_REDIRECT_URI` | Google OAuth Callback URL | `http://localhost:8000/api/auth/google/callback` |
| `OPENAI_API_KEY` | OpenAI API Key for GPT-4o tool calling | *(optional for fallback)* |
| `OPENAI_MODEL` | Model identifier | `gpt-4o-mini` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `SECRET_KEY` | JWT Signing secret | Dev secret |

> **Zero-Friction Evaluation Mode**:
> If Google or OpenAI API keys are not provided, the application runs in **Instant Demo Mode** with pre-seeded email threads (David, John, Sarah, last 10 days) and an **Intelligent Rule-Based Tool Calling Parser**. You can test every feature immediately without external accounts!

---

### Frontend (`frontend/.env.local`)

| Variable | Description | Value |
| :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Backend REST API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | Real-time WebSocket endpoint | `ws://localhost:8000/ws` |

---

## 🔑 Google Cloud OAuth Setup (Optional for Live Gmail)

To connect your real Gmail account:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named `AI-Mail-App`.
3. Enable the **Gmail API** in **APIs & Services > Library**.
4. Configure the **OAuth Consent Screen**:
   - User type: External.
   - Add scopes:
     - `openid`
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
     - `.../auth/gmail.readonly`
     - `.../auth/gmail.send`
     - `.../auth/gmail.modify`
   - Add your test Google email under Test Users.
5. Create Credentials:
   - **Credentials > Create Credentials > OAuth client ID**.
   - Application type: **Web application**.
   - Authorized redirect URIs:
     - `http://localhost:8000/api/auth/google/callback`
6. Copy the generated **Client ID** and **Client Secret** into `backend/.env`.

---

## 🤖 AI Agent Tools & Supported Flows

The assistant implements 6 core tools:

1. **`navigate_to_compose`**: Instructs client to route to `/compose`.
2. **`fill_compose_form(to, cc, bcc, subject, body)`**: Progressively fills the compose form with field-by-field typing animations.
3. **`search_emails(query, folder, days_ago)`**: Queries mailbox and updates active filters and results.
4. **`open_email(email_id)`**: Opens full message details on the client.
5. **`reply_to_email(email_id, body)`**: Context-aware thread reply generator with `Re:` prefix and populated recipient.
6. **`send_email(to, cc, bcc, subject, body)`**: Sends email via Gmail API and emits real-time WebSocket notifications.

### 5 Required Core Scenarios

#### Flow 1 — AI Compose
- **Command**: `"Compose an email to john@example.com with subject Meeting Tomorrow and body Let's meet at 3pm"`
- **Action**: Navigates to `/compose`, triggers visible character-by-character typing animation across `To`, `Subject`, and `Body`.
- **Safety Guard**: Drafting **never** sends automatically unless explicitly instructed.

#### Flow 2 — Search / Date Filtering
- **Command**: `"Show emails from the last 10 days"`
- **Action**: Queries backend database for emails received within the last 10 days and updates list and filter pills.

#### Flow 3 — Open Latest Email
- **Command**: `"Open the latest email from David"`
- **Action**: Searches emails from David, finds the newest email (`Project Roadmap & Q4 Milestones`), navigates to `/email/{id}`, and opens it.

#### Flow 4 — Context-Aware Reply
- **Command**: `"Reply to this email saying I will attend tomorrow's meeting"`
- **Action**: Detects currently opened email from client context, prepares reply to original sender with subject prefixed by `Re:`, and opens reply form with generated draft.

#### Flow 5 — Explicit Send
- **Command**: `"Send this email"`
- **Action**: Validates recipient and subject, sends email via Gmail API, saves local record with `is_sent=true`, broadcasts `email_sent` over WebSocket, and routes to `/sent`.

---

## 🧪 Testing

Run backend tests:
```bash
cd backend
venv\Scripts\python -m pytest tests -v
```
All 11 automated unit and integration tests verify:
- Health endpoint
- Email listing, sender filtering, and date range filtering
- Composing, sending, and sent folder verification
- Marking read/unread and star toggles
- AI Assistant tool calling (`navigate_to_compose`, `fill_compose_form`, `search_emails`, `open_email`, `reply_to_email`, `send_email`)
- Drafting vs sending safety enforcement

Verify frontend:
```bash
cd frontend
npm run build
```

---

## 🔧 Troubleshooting

1. **Port 8000 or 3000 already in use:**
   - Terminate the conflicting process or specify another port (`uvicorn app.main:app --port 8005`, `npm run dev -- -p 3005`).
2. **WebSocket connection issue:**
   - Ensure the backend is running on `http://localhost:8000` before loading the frontend.
3. **OpenAI Quota / Missing Key:**
   - The app automatically switches to the built-in natural language parser when `OPENAI_API_KEY` is not present, allowing full testing of all tools without interruption.
