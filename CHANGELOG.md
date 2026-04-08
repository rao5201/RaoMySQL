# RaoMySQL Changelog

## [1.2.0] - 2026-04-08

### Enhanced
- MySQL Client v1.1: Real SHOW STATUS metrics, slow query detection, capacity analysis
- Backup Service v1.1: Real DB dump execution with async tasks, SHA256 checksum, file download
- Monitor v1.1: Live metrics QPS buffer pool threads
- AI v1.1: LLM support OpenAI Ollama NL2SQL

### Added
- Audit Log: Full operation tracking with query/stats/cleanup APIs
- Data Export: CSV/JSON export for any table with column/where filters
- Docker: Updated configs with nginx reverse proxy, health checks, named volumes
- Deployment: DEPLOY.md guide, .env.example template

### Technical
- Python 3.14 FastAPI SQLAlchemy aiomysql
- React 19 Vite Ant Design 6 TypeScript

## [1.0.0] - 2026-04-06

### Added
- RaoCMS Enterprise Backend Multi-role permissions
- Article User Supplier Product Finance modules
- Backup Monitor Tasks AI Assistant features

## [0.1.0] - 2026-04-05

### Added
- Initial framework FastAPI JWT MySQL connections
- Credential storage
- Docker deployment
