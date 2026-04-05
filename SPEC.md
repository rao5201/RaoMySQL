# RaoMySQL — 私有 MySQL 数据库管理平台

## 1. 项目概述

- **项目名称**：RaoMySQL
- **定位**：私有化部署的 MySQL 数据库管理平台，服务于个人或小团队，不对外暴露
- **核心功能**：数据库连接管理、SQL 增删改查、备份恢复、用户权限管理、监控告警、数据可视化、定时任务、AI 智能操作
- **目标用户**：开发者/DBA，单人或多人的私有 MySQL 管理场景

---

## 2. 技术架构

### 2.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | React + Ant Design Pro | 专业级数据库管理 UI，企业风格 |
| **后端** | Python FastAPI | 高性能 API 框架，易集成 AI |
| **元数据库** | SQLite | 存储用户/连接配置/备份记录，无需额外安装 DB |
| **AI 引擎** | LangChain + OpenAI / 本地 LLM | 自然语言 SQL、自动化修复 |
| **任务调度** | APScheduler | 定时备份、健康巡检 |
| **部署** | Docker + Docker Compose | Linux 一键部署；Windows 直接运行 |

### 2.2 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React)                         │
│   SQL编辑器 / 结果表格 / 监控图表 / 用户管理 / AI对话     │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────────────┐
│                  后端 (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │  用户认证  │ │ 连接管理  │ │ SQL执行器 │ │  AI引擎   │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ 备份恢复  │ │  监控采集  │ │ 定时任务  │ │  告警模块  │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
  ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
  │  SQLite      │ │  MySQL      │ │  MySQL      │
  │  (元数据库)   │ │  实例 1      │ │  实例 N      │
  │  用户/连接    │ │  (受管理)    │ │  (受管理)    │
  └──────────────┘ └─────────────┘ └─────────────┘
```

---

## 3. 功能模块详细设计

### 3.1 用户与权限体系

**用户角色：**
| 角色 | 说明 |
|------|------|
| `admin` | 平台管理员，可管理所有数据库连接、所有用户 |
| `developer` | 可连接数据库，执行 SQL（增删改查），不能管理用户 |
| `viewer` | 只读权限，只能查询数据，不能执行写操作 |

**功能：**
- 用户注册（需管理员审核开启注册，或由管理员手动创建）
- 用户登录（JWT Token，Token 有效期 7 天，支持 Refresh Token）
- 密码修改、个人资料
- 管理员：新增/编辑/删除/禁用用户

### 3.2 数据库连接管理

- **连接配置**：支持 MySQL 5.7/8.x，填写 host/port/用户名/密码/数据库名
- **连接池**：后端维护连接池，避免频繁建立/断开连接
- **密码加密**：连接密码使用 AES-256 加密存储在 SQLite 中
- **SSL/TLS**：支持 SSL 连接选项
- **标签分组**：给数据库打标签（如：生产环境、测试环境、开发环境）
- **测试连接**：添加连接前测试连通性
- **支持数量**：单用户可管理 50+ 数据库实例

### 3.3 SQL 编辑器与执行器

- **语法高亮**：支持 MySQL 语法高亮（基于 CodeMirror 或 Monaco）
- **多标签页**：支持多个 SQL 编辑器标签页
- **执行方式**：支持整段执行、选中行执行
- **结果展示**：表格形式展示查询结果，支持分页（每页 100 条）
- **导出**：查询结果导出为 CSV / Excel
- **历史记录**：每次执行记录（SQL 内容、时间、用户、执行耗时、影响行数）
- **快捷键**：Ctrl+Enter 执行、Ctrl+S 保存 SQL 片段
- **SQL 片段收藏**：用户可保存常用 SQL 片段

### 3.4 数据可视化（仪表盘）

- **数据库概览**：每个连接展示基本信息（版本、字符集、连接数）
- **表结构浏览**：左侧树形展示库→表→字段结构
- **容量分析**：每个库的容量占用排行（Top 10 大表）
- **连接数监控**：实时连接数曲线图（每分钟采样，保留 24 小时）
- **慢查询统计**：Top 10 慢查询语句
- **健康评分**：综合评分（连接成功率、慢查询数量、容量使用率）

### 3.5 备份与恢复

- **手动备份**：选择数据库，一键导出 `.sql` 或 `.tar.gz`
- **定时备份**：配置备份策略（每日/每周/每月），自动执行
- **备份存储**：备份文件存储在本地指定目录（可配置 NAS 路径）
- **备份列表**：记录所有备份（时间、大小、状态）
- **一键恢复**：选择备份文件，恢复到指定数据库
- **备份校验**：备份完成后自动校验文件完整性

### 3.6 定时任务

- **任务类型**：
  - 数据库健康巡检（检查连接、慢查询、容量）
  - 定时备份
  - 定时发送监控报告
  - 定时清理历史日志/慢查询记录
- **调度策略**：Cron 表达式（支持任意时间周期）
- **任务日志**：每次执行记录成功/失败及输出
- **告警通知**：任务失败时发送通知（站内消息/邮件）

### 3.7 监控告警

- **监控指标**：
  - 连接数超限（默认 >80% 最大连接数）
  - 磁盘容量告警（默认 >85% 使用率）
  - 慢查询数量异常（超过阈值）
  - 数据库不可达（连接失败）
  - 备份失败
- **告警方式**：
  - 平台内实时通知（WebSocket 推送）
  - 邮件通知（可配置 SMTP）
- **告警历史**：记录所有告警，可查询和导出

### 3.8 AI 智能助手

- **自然语言转 SQL**：输入"帮我查一下过去一周注册用户最多的前10个表"，AI 生成 SQL 并执行
- **SQL 审查**：执行前 AI 给出风险评估（是 SELECT 还是 UPDATE/DELETE）
- **慢查询诊断**：AI 分析慢查询，给出优化建议（加索引、改写语句等）
- **自动修复**：AI 发现异常后给出修复方案，用户一键执行
- **智能告警**：AI 综合分析监控数据，给出预警和原因分析
- **对话界面**：独立的 AI 对话面板，支持追问和上下文

**AI 配置：**
- 默认接入 OpenAI GPT-4 / Claude
- 支持配置本地 LLM（如 Ollama + Llama3）
- 支持自定义 API Endpoint（适配各类 LLM 服务）

---

## 4. 数据模型

### 4.1 SQLite 元数据库表结构

```sql
-- 用户表
users (
  id          INTEGER PRIMARY KEY,
  username    VARCHAR(64) UNIQUE NOT NULL,
  password    VARCHAR(255) NOT NULL,  -- bcrypt 哈希
  role        VARCHAR(32) DEFAULT 'developer',
  email       VARCHAR(128),
  status      VARCHAR(16) DEFAULT 'active',  -- active/disabled
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME
)

-- 数据库连接表
db_connections (
  id           INTEGER PRIMARY KEY,
  user_id      INTEGER REFERENCES users(id),
  name         VARCHAR(128) NOT NULL,  -- 连接别名
  host         VARCHAR(255) NOT NULL,
  port         INT DEFAULT 3306,
  username     VARCHAR(128),
  password_enc VARCHAR(512),  -- AES-256 加密
  database_name VARCHAR(128),
  tags         VARCHAR(256),  -- 逗号分隔标签
  ssl_enabled  BOOLEAN DEFAULT FALSE,
  max_connections INT DEFAULT 100,
  created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at   DATETIME
)

-- SQL 执行历史
sql_history (
  id            INTEGER PRIMARY KEY,
  user_id       INTEGER REFERENCES users(id),
  connection_id INTEGER REFERENCES db_connections(id),
  sql_text      TEXT NOT NULL,
  sql_type      VARCHAR(16),  -- SELECT/INSERT/UPDATE/DELETE/DDL
  duration_ms   INT,
  rows_affected INT,
  status        VARCHAR(16),  -- success/error
  error_msg     TEXT,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- SQL 收藏片段
sql_snippets (
  id            INTEGER PRIMARY KEY,
  user_id       INTEGER REFERENCES users(id),
  name          VARCHAR(128),
  sql_text      TEXT NOT NULL,
  description   TEXT,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 备份记录
backups (
  id            INTEGER PRIMARY KEY,
  connection_id INTEGER REFERENCES db_connections(id),
  user_id       INTEGER REFERENCES users(id),
  file_path     VARCHAR(512),
  file_size     BIGINT,
  status        VARCHAR(16),  -- success/failed/running
  backup_type   VARCHAR(16),  -- manual/scheduled
  checksum      VARCHAR(64),  -- SHA256
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 定时任务
scheduled_tasks (
  id            INTEGER PRIMARY KEY,
  user_id       INTEGER REFERENCES users(id),
  name          VARCHAR(128),
  task_type     VARCHAR(64),  -- backup/health_check/report/cleanup
  cron_expr     VARCHAR(64),
  config        TEXT,  -- JSON 配置
  enabled       BOOLEAN DEFAULT TRUE,
  last_run_at   DATETIME,
  last_status   VARCHAR(16),
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 任务执行日志
task_runs (
  id            INTEGER PRIMARY KEY,
  task_id       INTEGER REFERENCES scheduled_tasks(id),
  status        VARCHAR(16),
  output        TEXT,
  started_at    DATETIME,
  finished_at   DATETIME
)

-- 告警记录
alerts (
  id            INTEGER PRIMARY KEY,
  user_id       INTEGER REFERENCES users(id),
  connection_id INTEGER REFERENCES db_connections(id),
  level         VARCHAR(16),  -- info/warning/critical
  title         VARCHAR(256),
  content       TEXT,
  status        VARCHAR(16) DEFAULT 'unread',  -- unread/read/resolved
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

## 5. API 设计（RESTful）

```
认证：
  POST   /api/auth/register        注册
  POST   /api/auth/login           登录
  POST   /api/auth/refresh          刷新 Token
  GET    /api/auth/me              当前用户信息

用户管理（admin）：
  GET    /api/users                用户列表
  POST   /api/users                创建用户
  PUT    /api/users/{id}           更新用户
  DELETE /api/users/{id}           删除用户

数据库连接：
  GET    /api/connections          连接列表
  POST   /api/connections           添加连接
  PUT    /api/connections/{id}      更新连接
  DELETE /api/connections/{id}      删除连接
  POST   /api/connections/{id}/test  测试连接
  GET    /api/connections/{id}/schema  获取库表结构

SQL 执行：
  POST   /api/query                执行 SQL
  GET    /api/query/history         执行历史
  GET    /api/query/tables          获取表列表

备份恢复：
  GET    /api/backups              备份列表
  POST   /api/backups              创建备份
  POST   /api/backups/{id}/restore  恢复备份
  DELETE /api/backups/{id}          删除备份

定时任务：
  GET    /api/tasks                 任务列表
  POST   /api/tasks                 创建任务
  PUT    /api/tasks/{id}            更新任务
  DELETE /api/tasks/{id}            删除任务
  POST   /api/tasks/{id}/run        立即执行

监控：
  GET    /api/monitor/{connection_id}/status    实时状态
  GET    /api/monitor/{connection_id}/slow-queries 慢查询
  GET    /api/monitor/{connection_id}/capacity   容量分析

告警：
  GET    /api/alerts                告警列表
  PUT    /api/alerts/{id}/read      标记已读
  PUT    /api/alerts/{id}/resolve   标记解决

AI：
  POST   /api/ai/chat               AI 对话
  POST   /api/ai/nl2sql             自然语言转 SQL
  POST   /api/ai/analyze-slow       分析慢查询
  GET    /api/ai/config             AI 配置
  PUT    /api/ai/config             更新 AI 配置
```

---

## 6. 前端页面结构

```
登录 / 注册
├── 仪表盘（首页）
│   ├── 健康评分总览
│   ├── 连接数实时图表
│   ├── 最新告警
│   └── 待办任务
├── 数据库连接管理
│   ├── 连接列表（标签筛选）
│   ├── 添加/编辑连接
│   └── 连接详情 → SQL 编辑器
├── SQL 编辑器
│   ├── 多标签页
│   ├── 表结构树（左侧）
│   ├── SQL 历史
│   └── 收藏片段
├── 备份中心
│   ├── 备份记录列表
│   ├── 创建备份
│   └── 恢复操作
├── 定时任务
│   ├── 任务列表
│   ├── 新建任务
│   └── 任务日志
├── 监控中心
│   ├── 数据库状态概览
│   ├── 慢查询分析
│   └── 容量分析图表
├── 告警中心
│   ├── 告警列表
│   └── 告警配置
├── AI 助手
│   └── 对话界面（集成 SQL 编辑器）
└── 系统设置（admin）
    ├── 用户管理
    ├── AI 配置
    ├── 备份存储配置
    └── SMTP 邮件配置
```

---

## 7. 部署方案

### 7.1 Windows 部署（本地开发/个人使用）

```bash
# 1. 安装 Python 3.10+
python --version

# 2. 克隆项目
git clone git@github.com:rao5201/RaoMySQL.git
cd RaoMySQL

# 3. 安装后端依赖
pip install -r backend/requirements.txt

# 4. 安装前端依赖
cd frontend
npm install

# 5. 启动后端
cd ../backend
python main.py

# 6. 启动前端（新窗口）
cd frontend
npm run dev
```

### 7.2 Linux 云服务器部署（Docker）

```bash
# 一键部署
docker-compose up -d

# 访问地址：http://服务器IP:3000
```

---

## 8. 开发阶段规划

### Phase 1 — 基础框架（第 1-2 周）
- [ ] 项目结构初始化（前后端分离）
- [ ] 用户认证（注册/登录/JWT）
- [ ] 数据库连接管理（加密存储/连接测试）
- [ ] SQL 编辑器基础版

### Phase 2 — 核心功能（第 3-4 周）
- [ ] SQL 执行与结果展示（多标签/分页/导出）
- [ ] 表结构浏览（库→表→字段）
- [ ] 备份与恢复
- [ ] 基础监控（连接数/容量）

### Phase 3 — 高级功能（第 5-6 周）
- [ ] 定时任务调度
- [ ] 告警系统
- [ ] 仪表盘数据可视化
- [ ] 用户权限管理

### Phase 4 — AI 能力（第 7-8 周）
- [ ] 自然语言转 SQL
- [ ] 慢查询 AI 分析
- [ ] 智能告警对话
- [ ] 自动修复建议

---

## 9. 目录结构

```
RaoMySQL/
├── SPEC.md
├── README.md
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── requirements.txt
│   ├── config.py            # 配置管理
│   ├── database/
│   │   ├── init_db.py       # SQLite 初始化
│   │   └── models.py        # 数据模型
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── connections.py
│   │   ├── sql.py
│   │   ├── backups.py
│   │   ├── tasks.py
│   │   ├── monitor.py
│   │   ├── alerts.py
│   │   └── ai.py
│   ├── services/
│   │   ├── mysql_client.py  # MySQL 连接管理
│   │   ├── backup.py        # 备份服务
│   │   ├── monitor.py       # 监控采集
│   │   ├── scheduler.py      # 定时任务
│   │   ├── ai_engine.py      # AI 引擎
│   │   └── crypto.py        # 加密工具
│   └── utils/
│       └── helpers.py
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Connections.tsx
│   │   │   ├── SqlEditor.tsx
│   │   │   ├── Backups.tsx
│   │   │   ├── Tasks.tsx
│   │   │   ├── Monitor.tsx
│   │   │   ├── Alerts.tsx
│   │   │   ├── AIAssistant.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── Layout.tsx
│   │   │   ├── SqlEditor.tsx
│   │   │   ├── DataGrid.tsx
│   │   │   └── ...
│   │   ├── api/
│   │   │   └── index.ts
│   │   └── store/
│   └── vite.config.ts
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── docker-compose.yml
└── docs/
    └── API.md
```

---

## 10. 安全设计

1. **传输安全**：全站强制 HTTPS（生产环境）
2. **密码安全**：bcrypt 哈希，不明文存储
3. **连接密码**：AES-256-GCM 加密存储，密钥由环境变量注入
4. **权限控制**：JWT + 角色鉴权，细粒度 API 权限
5. **SQL 安全**：禁止执行危险操作（LOAD_FILE/SYSTEM_USER 等），防止 SQL 注入
6. **审计日志**：所有操作记录到日志文件
7. **私有部署**：平台不出网，所有数据留在本地

---

*最后更新：2026-04-05*
