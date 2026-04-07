# Bind RP Agent — Atollom AI

Dashboard de inteligencia operativa y financiera conectado a Bind ERP.

## Stack
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS → Vercel
- **Backend:** FastAPI (Python) → Railway/Render
- **Auth + DB:** Supabase
- **ERP:** Bind ERP API

## Setup Rápido

### Backend
```bash
cd backend
cp .env.example .env   # Llenar variables reales
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local  # Llenar variables reales
npm install
npm run dev
```

## Variables de Entorno

Ver `backend/.env.example` y `frontend/.env.local.example`.
