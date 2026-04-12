# RaoMySQL
https://raomysql.pages.dev/

Private MySQL Database Management Platform

## Version
**v1.3.0** (2026-04-08)

## Features
- Database connection management (CRUD)
- SQL execution
- Backup & restore
- User permission management
- Monitoring & alerts
- AI integration (NL2SQL, slow query analysis, SQL review)
- Unified user system across RaoMySQL/RaoCMS/RaoFileManager

## Tech Stack
- Backend: Python FastAPI + SQLAlchemy
- Frontend: React 18 + TypeScript + Vite + Ant Design
- Database: SQLite (metadata) + MySQL (target)
- Deployment: Docker + Nginx

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

## Docker
`ash
docker-compose up -d
`

## Default Admin
- Username: admin
- Password: admin123

## Related Projects
- RaoCMS - Enterprise CMS/ERP
- RaoFileManager - File Management System

---
Unified user system connects RaoMySQL, RaoCMS, RaoFileManager.
