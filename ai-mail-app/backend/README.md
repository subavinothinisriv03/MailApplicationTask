# AI Mail App — Backend

Production-ready FastAPI backend for the AI-Powered Mail Web Application. Features Google OAuth 2.0, Gmail REST API synchronization, real-time WebSockets, and an OpenAI tool-calling agent that actively controls the user interface.

---

## 🚀 Quick Start

### 1. Create Virtual Environment

From the `backend/` directory:

```bash
cd backend
python -m venv venv
```

**Activate on Windows (PowerShell / Command Prompt):**
```powershell
venv\Scripts\activate
```

**Activate on macOS / Linux:**
```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
APP_NAME=AI Mail App
ENVIRONMENT=development
DATABASE_URL=sqlite:///./mail.db

FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback

OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini

CORS_ORIGINS=http://localhost:3000
SECRET_KEY=dev-secret-key-change-in-production-1234567890
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

> **Note on Zero-Friction Local Testing**:
> If `GOOGLE_CLIENT_ID` or `OPENAI_API_KEY` are not yet filled, the application includes a **1-Click Demo Mode** and an **Intelligent Rule Parser fallback**. You can launch and test all API routes, WebSocket events, and UI control actions immediately out of the box!

### 4. Run the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📡 API Overview

### 🔐 Authentication (`/api/auth`)
- `GET /api/auth/google/login`: Redirects to Google OAuth 2.0 consent screen.
- `GET /api/auth/google/callback`: Exchanges auth code for tokens and issues session JWT.
- `POST /api/auth/demo-login`: Instant 1-click test login.
- `GET /api/auth/me`: Returns current user profile.
- `POST /api/auth/logout`: Clears authentication session.

### ✉️ Emails (`/api/emails`)
- `GET /api/emails`: List emails with query, sender, date range, read/starred filters, and pagination.
- `GET /api/emails/inbox`: Quick access to received emails.
- `GET /api/emails/sent`: Sent emails list.
- `GET /api/emails/search?q=...`: Search across senders, subjects, and bodies.
- `GET /api/emails/{id}`: Detailed view (automatically marks as read).
- `POST /api/emails`: Compose and send email via Gmail API.
- `POST /api/emails/{id}/read` & `unread`: Toggle read status.
- `POST /api/emails/{id}/star` & `unstar`: Toggle starred status.
- `POST /api/emails/{id}/reply`: Reply to an email thread.
- `DELETE /api/emails/{id}`: Trash / delete email.

### 🤖 AI Agent (`/api/assistant`)
- `POST /api/assistant/chat`: Processes natural language instructions with client context (`current_view`, `current_email_id`, `draft_state`, `current_filters`). Triggers OpenAI tool calling, executes operations against DB/Gmail, and emits structured UI actions.
- `GET /api/assistant/history`: Retrieve conversation transcript.
- `DELETE /api/assistant/history`: Clear conversation session.

### ⚡ WebSocket (`/ws`)
- `ws://localhost:8000/ws` or `ws://localhost:8000/ws?token=<jwt>`: Real-time event stream broadcasting `email_sent`, `email_updated`, `tool_action`, and `typing` notifications.

---

## 🛠️ Registered AI Tools
1. `navigate_to_compose()`: Tells frontend to navigate to `/compose`.
2. `fill_compose_form(to, cc, bcc, subject, body)`: Visibly populates compose fields.
3. `search_emails(query, folder, days_ago)`: Queries mailbox and updates view.
4. `open_email(email_id)`: Opens selected email on the frontend.
5. `reply_to_email(email_id, body)`: Prepares thread reply with `Re:` prefix and draft content.
6. `send_email(to, cc, bcc, subject, body)`: Explicitly sends email via Gmail.
