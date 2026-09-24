# AI Mail App — Frontend

Modern Next.js 15 App Router web client with real-time WebSocket sync and an AI Assistant that actively controls the interface.

---

## 🛠️ Tech Stack
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS with dark mode
- **State Management**: Zustand
- **Icons**: Lucide React
- **Real-Time**: Native WebSocket client with auto-reconnection

---

## 🚀 Setup & Development

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```
Content:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

### 3. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🤖 Features
- **AI UI Control**: The AI Assistant directly navigates views, searches and filters emails, opens messages, and types drafts progressively with realistic field-by-field typing animations.
- **Real-Time Updates**: WebSockets push newly received emails and sent messages directly into the UI without page refreshes.
- **Inbox & Sent Views**: Filter by keyword, sender, date range (e.g., last 10 days), and read/starred status.
- **Thread Reply & Compose**: Seamlessly compose new emails or generate context-aware replies to open threads.
- **Dark Mode**: Persisted theme preferences (Light / Dark / System).
