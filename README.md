# RaoMySQL
https://raomysql.pages.dev/

Private MySQL Database Management Platform
# RaoMySQL Changelog

## v1.6.0 - 网站上线与注册系统 (2026-04-12)

### ✨ 新功能

- **官方宣传网站上线** — 深海极客风格落地页（raomysql.pages.dev），粒子网络动画、功能展示、版本时间线
- **用户邀请码注册系统** — `POST /api/auth/register` 支持邀请码验证，后台可管理邀请码
- **Cloudflare Pages 自动化部署** — `build.sh` 构建脚本，自动合并落地页 + React SPA 到统一 `dist/` 目录
- **落地页注册/登录直达链接** — 用户从落地页一键跳转注册或登录
- **管理后台"返回首页"导航** — 侧边栏 Logo + 顶部 Header 均可返回网站首页

### 🔧 技术变更

- `index.html` — 官方宣传落地页（41KB）
- `build.sh` — Cloudflare Pages 构建脚本
- `frontend/vite.config.ts` — outDir 改为 `../dist`，base 改为 `./`（相对路径适配）
- `frontend/src/App.tsx` — BrowserRouter → HashRouter（适配 Cloudflare Pages）
- `.gitignore` — 新增 `dist/`、`frontend/node_modules/`

### 🌐 部署

- 网站地址：https://raomysql.pages.dev/
- 构建命令：`bash build.sh`
- 输出目录：`dist`
- 结构：`index.html`（落地页）+ `app.html`（React 管理后台 SPA）

---

## v1.5.0 - 后端修复与可用版本 (2026-04-12)

### 🐛 Bug 修复

- **Python 导入路径问题** — 统一改为 `backend.xxx` 包格式，修复 `ModuleNotFoundError`
- **uvicorn 模块启动问题** — `main.py` 添加 `sys.path.insert(0, parent)` 解决路径解析
- **路由前缀重复** — 移除 `include_router` 中冗余的 `prefix="/api"`，解决 `/api/api/auth` 路径问题
- **配置属性缺失** — `settings.PORT` 改为硬编码 `8000`
- **bcrypt 兼容性问题** — `bcrypt 5.0.0` + `passlib` 冲突导致 500 错误，新增 `sha256_crypt` 备用方案自动降级

### ✅ 验证通过

- `POST /api/auth/register` → 200 OK（用户注册）
- `POST /api/auth/login` → 200 OK + JWT Token（用户登录）
- `GET /api/auth/me` → 返回当前用户信息

### 🔧 技术变更

- 19 个后端文件导入路径统一修复
- 新增 `.gitignore`（忽略 `__pycache__`、`*.pyc`、`raomysql.db`）
- 新增 `sha256_crypt` 备用密码哈希方案（`auth.py`）

---

## v1.4.0 - 用户管理版本 (2026-04-09)

### 新功能

- **用户注册页面** (`Register.tsx`)
  - 表单验证（用户名格式/密码强度/邮箱格式）
  - 两步密码确认
  - 自动登录跳转

- **用户管理面板** (`Users.tsx`)
  - 用户列表：分页 / 角色筛选 / 状态筛选 / 关键词搜索
  - 添加用户：用户名 / 邮箱 / 角色 / 初始密码
  - 编辑用户：修改角色、状态
  - 重置密码：管理员一键重置并显示新密码
  - 启用/禁用：一键切换用户状态
  - 删除用户：带确认提示（不可删除自己）
  - 统计卡片：总用户 / 正常 / 禁用 / 管理员数量

- **用户管理后端 API** (`routers/users.py`)
  - `GET /api/users` - 用户列表（分页 + 筛选）
  - `POST /api/users` - 创建用户
  - `GET/PUT/DELETE /api/users/{id}` - 查看/编辑/删除
  - `POST /api/users/{id}/reset-password` - 重置密码
  - `POST /api/users/{id}/toggle-status` - 启用/禁用
  - `GET /api/users/stats/overview` - 统计概览
  - `POST /api/users/me/change-password` - 用户改自己密码

### 技术升级
- `backend/routers/users.py` - 完整用户 CRUD API
- `frontend/src/pages/Register.tsx` - 注册页面
- `frontend/src/pages/Users.tsx` - 用户管理面板
- `frontend/src/App.tsx` - 新路由 /users、/register

---

## v1.3.0 - 统一用户体系版本 (2026-04-08)

### 新功能
- 统一用户认证系统
- 跨系统单点登录
- 统一 API Gateway
- 跨系统数据关联

### 技术升级
- `unified_auth.py` - 统一认证服务
- `unified_models.py` - 统一用户模型
- `cross_links.py` - 跨系统数据关联
- `gateway.py` - API 网关

---

## v1.2.0 - AI 与监控版本 (2026-04-08)
- AI 助手 / AI 设置页面
- 审计日志看板
- 数据导出功能

---

## v1.1.0 - 企业 CMS 版本 (2026-04-06)
- 企业内容管理基础功能

---

## v1.0.0 - 初始版本 (2026-04-05)
- MySQL 连接管理
- SQL 执行器
- 基础权限体系

## Version
**v1.6.0** (2026-04-12)

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
