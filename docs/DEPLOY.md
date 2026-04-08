# ============================================
# RaoMySQL v1.2.0 Deployment Guide
# ============================================

## Quick Start (Docker)

```bash
cd docker

# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Manual Setup (Development)

### Backend
```bash
cd backend
pip install -r requirements.txt
# Set env vars or create .env
python main.py
# API Docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# http://localhost:5173
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| SECRET_KEY | change-me | Yes | JWT signing key |
| ENCRYPTION_KEY | 32-byte-... | Yes | AES credential encryption key (32+ chars) |
| OPENAI_API_KEY | (empty) | No | For AI assistant |
| AI_PROVIDER | openai | No | openai / ollama |
| AI_MODEL | gpt-4 | No | LLM model name |
| AI_ENDPOINT | (empty) | No | Custom LLM endpoint (required for ollama) |
| PORT | 8000 | No | Backend server port |

## Docker Volumes
- `backend_data` → /app/data (SQLite DB + backup files)

## Default Admin Account
- Username: admin
- Credential: admin123

## Production Checklist
- [ ] Change SECRET_KEY to a random 64-char string
- [ ] Change ENCRYPTION_KEY to a random 32+ char string
- [ ] Set OPENAI_API_KEY if AI features needed
- [ ] Configure CORS origins (currently allow *)
- [ ] Set up SSL/TLS termination (nginx/Caddy)
- [ ] Configure automated backups
- [ ] Set up monitoring alerts
