# RaoMySQL Changelog

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
