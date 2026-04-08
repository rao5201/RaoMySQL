# RaoMySQL v1.2.0

> Private MySQL Database Management Platform + Enterprise CMS
> Author: [Rao](https://github.com/rao5201)
> License: MIT

## Features

| Module | Description |
|--------|------------|
| MySQL Management | Connection pool, SQL editor, credential encryption |
| Backup and Restore | DB dump with checksum verification |
| Monitoring | Real-time SHOW STATUS, slow queries, capacity |
| Scheduled Tasks | Cron-based task scheduling |
| AI Assistant | NL2SQL, slow query analysis (OpenAI/Ollama) |
| CMS Backend | Multi-role, article/user/supplier/product/finance |

## Quick Start

`ash
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
`

## Tech Stack

- Backend: Python 3.14 / FastAPI / SQLAlchemy / aiomysql
- Frontend: React 19 / Vite / Ant Design 6 / TypeScript
- Database: SQLite (meta) + MySQL (managed)
- Security: JWT + AES-256-GCM + RBAC

## Project Structure

`
RaoMySQL/
  backend/
    main.py
    config.py
    database/
    routers/
    services/
    utils/
  frontend/
    src/pages/
  docker/
`
