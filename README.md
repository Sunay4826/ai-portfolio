# AI Portfolio Website (React + TypeScript + Python + SQLite + OpenRouter)

This project is an internship-ready personal portfolio website with AI chat functionality that answers user questions based on your resume.

## Live Deployment
- Frontend: https://ai-portfolio-five-alpha.vercel.app
- Backend: https://ai-portfolio-xq5b.onrender.com

## Tech Stack
- Frontend: React + TypeScript (Vite)
- Backend: Python + FastAPI
- Database: SQLite (via SQLAlchemy)
- Chat Engine: OpenRouter (free model configurable)

## Project Structure
- `/frontend` - Portfolio UI + chat widget
- `/backend` - FastAPI API, SQLite persistence, OpenRouter integration

## 1) Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set one of the following:
- `OPENROUTER_API_KEY` (must start with `sk-or-v1-`)
- or `GEMINI_API_KEY` (Google Gemini API key)

Optional model vars:
- `OPENROUTER_MODEL` (default free model is included)
- `GEMINI_MODEL` (default: `gemini-1.5-flash`)

Start backend:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 2) Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Frontend default URL: `http://localhost:5173`

## 3) Update Resume Context
Replace the content in:
- `backend/resume.md`

This file is used as the source of truth for chat answers.

## API Endpoints
- `GET /health`
- `POST /api/chat` - body: `{ "question": "..." }`
- `GET /api/chat/history`

## Bonus Deployment (Public Access)

### Option A: Cloudflare Tunnel (free)
Run locally and expose the frontend:
```bash
cloudflared tunnel --url http://localhost:5173
```

### Option B: GitHub
1. Push code to a public GitHub repo.
2. Add screenshots and project demo link in repo README.
3. Optionally deploy frontend to Vercel/Netlify and backend to Render/Fly/Railway free tiers.

## Notes
- The assistant is instructed to answer only from resume context.
- If a fact is missing, it should say it is not listed.
- Backend prefers OpenRouter when a valid OpenRouter key exists; otherwise it falls back to Gemini when `GEMINI_API_KEY` is set.
