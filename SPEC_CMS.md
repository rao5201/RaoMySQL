# RaoCMS — 企业网站后台管理系统

## 1. 项目概述

- **项目名称**：RaoCMS
- **定位**：企业级网站内容管理系统，支持多角色权限管理
- **核心功能**：文章管理、文件管理、用户管理、供应商管理、产品管理、财务分析、注册用户信息库
- **目标用户**：企业内容运营团队、客服、财务、管理员

---

## 2. 角色权限体系

| 角色 | 权限范围 | 说明 |
|------|---------|------|
| **访客/前台用户** | 仅浏览公开内容 | 无后台权限 |
| **客服** | 查看文章、查看文件、添加文章、上传文件 | 需管理员审核后才能公开 |
| **管理员** | 全部权限 | 系统最高权限，管理所有模块 |
| **财务/审计** | 查看销售分析、费用分析、财务对接模块 | 查看所有财务相关数据 |

### 权限矩阵

| 功能模块 | 访客 | 客服 | 财务 | 管理员 |
|---------|:----:|:----:|:----:|:------:|
| 文章浏览 | ✅ | ✅ | ✅ | ✅ |
| 文章添加 | ❌ | ✅(需审核) | ❌ | ✅ |
| 文章编辑 | ❌ | ❌ | ❌ | ✅ |
| 文章删除 | ❌ | ❌ | ❌ | ✅ |
| 文章审核 | ❌ | ❌ | ❌ | ✅ |
| 文件浏览 | ❌ | ✅ | ❌ | ✅ |
| 文件上传 | ❌ | ✅ | ❌ | ✅ |
| 文件删除 | ❌ | ❌ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ❌ | ✅ |
| 供应商管理 | ❌ | ❌ | ✅ | ✅ |
| 产品管理 | ❌ | ❌ | ✅ | ✅ |
| 销售分析 | ❌ | ❌ | ✅ | ✅ |
| 费用分析 | ❌ | ❌ | ✅ | ✅ |
| 财务报表 | ❌ | ❌ | ✅ | ✅ |
| 注册用户信息 | ❌ | ❌ | ❌ | ✅ |
| 系统设置 | ❌ | ❌ | ❌ | ✅ |

---

## 3. 功能模块设计

### 3.1 内容管理

#### 文章管理
- **栏目分类**：支持多级栏目（新闻动态、产品中心、关于我们、帮助中心等）
- **文章状态**：草稿、待审核、已发布、已驳回、已下架
- **富文本编辑**：支持图文混排、附件插入、SEO 设置
- **审核流程**：客服添加 → 管理员审核 → 公开发布

#### 文件管理
- **文件类型**：图片、文档、视频、压缩包等
- **存储方式**：本地存储 + 可选云存储（OSS/S3）
- **文件标签**：支持分类标签管理

### 3.2 用户管理

#### 注册用户管理
- **用户信息**：注册时间、最后登录、联系方式、用户标签
- **用户分析**：注册趋势、活跃度分析、地域分布
- **用户分组**：VIP用户、普通用户、黑名单

#### 后台用户管理
- **账号管理**：创建、编辑、禁用、删除
- **角色分配**：客服、财务、管理员
- **操作日志**：记录所有后台操作

### 3.3 供应商管理

- **供应商信息**：公司名称、联系人、联系方式、合作状态
- **合作记录**：合同、订单、付款记录
- **供应商评级**：评分、评价、合作历史
- **分析看板**：供应商分布、合作金额统计

### 3.4 产品管理

- **产品信息**：名称、分类、价格、库存、SKU
- **产品状态**：上架、下架、缺货
- **销售数据**：销量、销售额、退货率
- **分析看板**：热销排行、库存预警、销售趋势

### 3.5 财务管理

#### 销售分析
- 销售额趋势（日/周/月/年）
- 订单量统计
- 客单价分析
- 支付方式分布

#### 费用分析
- 运营成本
- 营销费用
- 人力成本
- 供应商付款

#### 财务对接
- 收支明细
- 应收应付
- 利润分析
- 财务报表导出

---

## 4. 技术架构

### 4.1 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **前端** | React + Ant Design Pro | 企业级后台管理 UI |
| **后端** | Python FastAPI | 高性能 API 框架 |
| **数据库** | SQLite（元数据）+ MySQL（业务数据） | 双数据库架构 |
| **文件存储** | 本地/MinIO/OSS | 可配置 |
| **任务调度** | APScheduler | 定时任务 |
| **部署** | Docker + Docker Compose | 一键部署 |

### 4.2 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React)                         │
│   仪表盘 / 文章管理 / 用户管理 / 供应商 / 产品 / 财务    │
└─────────────────────────┬───────────────────────────────┘
                          │ HTTP
┌─────────────────────────▼───────────────────────────────┐
│                  后端 (FastAPI)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │  用户认证  │ │ 内容管理  │ │ 文件管理  │ │  用户管理  │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐ │
│  │ 供应商管理 │ │ 产品管理  │ │ 财务分析  │ │  审核流程  │ │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘ │
└─────────────────────────┬───────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
  ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
  │  SQLite      │ │  MySQL      │ │  文件存储    │
  │  (系统配置)   │ │  (业务数据)  │ │  (本地/OSS) │
│  用户/权限    │ │  文章/产品   │ │             │
  └──────────────┘ └─────────────┘ └─────────────┘
```

---

## 5. 数据模型

### 5.1 用户相关

```sql
-- 后台用户表
sys_users (
  id          INTEGER PRIMARY KEY,
  username    VARCHAR(64) UNIQUE NOT NULL,
  password    VARCHAR(255) NOT NULL,
  real_name   VARCHAR(64),
  role        VARCHAR(32) DEFAULT 'customer_service', -- admin/customer_service/finance
  email       VARCHAR(128),
  phone       VARCHAR(32),
  avatar      VARCHAR(512),
  status      VARCHAR(16) DEFAULT 'active', -- active/disabled
  last_login  DATETIME,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 前台注册用户表
portal_users (
  id          INTEGER PRIMARY KEY,
  username    VARCHAR(64) UNIQUE NOT NULL,
  password    VARCHAR(255) NOT NULL,
  email       VARCHAR(128),
  phone       VARCHAR(32),
  nickname    VARCHAR(64),
  avatar      VARCHAR(512),
  status      VARCHAR(16) DEFAULT 'active',
  user_tags   VARCHAR(256), -- 逗号分隔标签
  register_ip VARCHAR(64),
  last_login  DATETIME,
  login_count INT DEFAULT 0,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 操作日志表
operation_logs (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER,
  user_type   VARCHAR(16), -- sys/portal
  action      VARCHAR(64), -- 操作类型
  module      VARCHAR(64), -- 操作模块
  detail      TEXT,        -- 操作详情
  ip_address  VARCHAR(64),
  user_agent  VARCHAR(512),
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 5.2 内容相关

```sql
-- 栏目分类表
categories (
  id          INTEGER PRIMARY KEY,
  parent_id   INTEGER DEFAULT 0,
  name        VARCHAR(128) NOT NULL,
  slug        VARCHAR(128) UNIQUE,
  description TEXT,
  sort_order  INT DEFAULT 0,
  status      VARCHAR(16) DEFAULT 'active',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 文章表
articles (
  id          INTEGER PRIMARY KEY,
  category_id INTEGER,
  title       VARCHAR(256) NOT NULL,
  slug        VARCHAR(256),
  summary     TEXT,
  content     TEXT,
  cover_image VARCHAR(512),
  author_id   INTEGER, -- 后台用户ID
  author_name VARCHAR(64),
  status      VARCHAR(16) DEFAULT 'draft', -- draft/pending/approved/rejected/published/offline
  is_top      BOOLEAN DEFAULT FALSE,
  view_count  INT DEFAULT 0,
  seo_title   VARCHAR(256),
  seo_keywords VARCHAR(256),
  seo_description TEXT,
  published_at DATETIME,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME
)

-- 文章审核记录
article_audits (
  id          INTEGER PRIMARY KEY,
  article_id  INTEGER,
  operator_id INTEGER,
  action      VARCHAR(32), -- submit/approve/reject/offline
  comment     TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 文件资源表
media_files (
  id          INTEGER PRIMARY KEY,
  user_id     INTEGER,
  filename    VARCHAR(256),
  original_name VARCHAR(256),
  file_path   VARCHAR(512),
  file_url    VARCHAR(512),
  file_type   VARCHAR(64), -- image/document/video/audio/other
  file_size   BIGINT,
  mime_type   VARCHAR(128),
  tags        VARCHAR(256),
  usage_count INT DEFAULT 0,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 5.3 供应商相关

```sql
-- 供应商表
suppliers (
  id          INTEGER PRIMARY KEY,
  name        VARCHAR(256) NOT NULL,
  code        VARCHAR(64) UNIQUE,
  contact_name VARCHAR(128),
  contact_phone VARCHAR(32),
  contact_email VARCHAR(128),
  address     TEXT,
  status      VARCHAR(16) DEFAULT 'active', -- active/inactive/blacklisted
  rating      DECIMAL(2,1) DEFAULT 5.0, -- 1-5分
  total_amount DECIMAL(15,2) DEFAULT 0, -- 累计合作金额
  remark      TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 供应商合作记录
supplier_records (
  id          INTEGER PRIMARY KEY,
  supplier_id INTEGER,
  record_type VARCHAR(32), -- contract/order/payment
  title       VARCHAR(256),
  amount      DECIMAL(15,2),
  status      VARCHAR(32),
  start_date  DATE,
  end_date    DATE,
  attachment  VARCHAR(512),
  remark      TEXT,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 5.4 产品相关

```sql
-- 产品分类表
product_categories (
  id          INTEGER PRIMARY KEY,
  parent_id   INTEGER DEFAULT 0,
  name        VARCHAR(128) NOT NULL,
  code        VARCHAR(64),
  sort_order  INT DEFAULT 0,
  status      VARCHAR(16) DEFAULT 'active',
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 产品表
products (
  id          INTEGER PRIMARY KEY,
  category_id INTEGER,
  name        VARCHAR(256) NOT NULL,
  code        VARCHAR(64) UNIQUE,
  description TEXT,
  price       DECIMAL(12,2),
  cost_price  DECIMAL(12,2),
  stock       INT DEFAULT 0,
  unit        VARCHAR(32),
  images      TEXT, -- JSON 数组
  status      VARCHAR(16) DEFAULT 'active', -- active/inactive/out_of_stock
  sales_count INT DEFAULT 0,
  view_count  INT DEFAULT 0,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at  DATETIME
)

-- 销售记录表
sales_records (
  id          INTEGER PRIMARY KEY,
  product_id  INTEGER,
  order_no    VARCHAR(64),
  quantity    INT,
  unit_price  DECIMAL(12,2),
  total_amount DECIMAL(12,2),
  user_id     INTEGER, -- 前台用户
  status      VARCHAR(32), -- pending/paid/shipped/completed/cancelled/refunded
  pay_method  VARCHAR(32),
  pay_time    DATETIME,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### 5.5 财务相关

```sql
-- 收支记录表
finance_records (
  id          INTEGER PRIMARY KEY,
  record_type VARCHAR(16), -- income/expense
  category    VARCHAR(64), -- 分类：销售/退款/运营/营销/人力/供应商等
  amount      DECIMAL(15,2),
  title       VARCHAR(256),
  description TEXT,
  related_id  INTEGER, -- 关联ID（订单ID/供应商ID等）
  related_type VARCHAR(64), -- 关联类型
  operator_id INTEGER,
  record_date DATE,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)

-- 财务报表缓存（日统计）
finance_daily_stats (
  id          INTEGER PRIMARY KEY,
  stat_date   DATE UNIQUE,
  income      DECIMAL(15,2) DEFAULT 0,
  expense     DECIMAL(15,2) DEFAULT 0,
  order_count INT DEFAULT 0,
  user_count  INT DEFAULT 0,
  created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

---

## 6. API 设计

### 认证相关
```
POST   /api/auth/login              登录
POST   /api/auth/logout             登出
GET    /api/auth/me                 当前用户信息
PUT    /api/auth/password           修改密码
```

### 用户管理（管理员）
```
GET    /api/users                   用户列表
POST   /api/users                   创建用户
PUT    /api/users/{id}              更新用户
DELETE /api/users/{id}              删除用户
GET    /api/users/{id}/logs         用户操作日志
```

### 前台用户管理
```
GET    /api/portal/users            注册用户列表
GET    /api/portal/users/{id}       用户详情
PUT    /api/portal/users/{id}       更新用户
GET    /api/portal/users/stats      用户统计
```

### 内容管理
```
GET    /api/categories              栏目列表
POST   /api/categories              创建栏目
PUT    /api/categories/{id}         更新栏目
DELETE /api/categories/{id}         删除栏目

GET    /api/articles                文章列表
POST   /api/articles                创建文章
GET    /api/articles/{id}           文章详情
PUT    /api/articles/{id}           更新文章
DELETE /api/articles/{id}           删除文章
POST   /api/articles/{id}/submit    提交审核
POST   /api/articles/{id}/approve   审核通过
POST   /api/articles/{id}/reject    审核驳回
POST   /api/articles/{id}/offline   下架文章
```

### 文件管理
```
POST   /api/media/upload            上传文件
GET    /api/media                   文件列表
DELETE /api/media/{id}              删除文件
```

### 供应商管理
```
GET    /api/suppliers               供应商列表
POST   /api/suppliers               创建供应商
GET    /api/suppliers/{id}          供应商详情
PUT    /api/suppliers/{id}          更新供应商
DELETE /api/suppliers/{id}          删除供应商
GET    /api/suppliers/{id}/records  合作记录
POST   /api/suppliers/{id}/records  添加合作记录
GET    /api/suppliers/stats         供应商统计
```

### 产品管理
```
GET    /api/products                产品列表
POST   /api/products                创建产品
GET    /api/products/{id}           产品详情
PUT    /api/products/{id}           更新产品
DELETE /api/products/{id}           删除产品
GET    /api/products/stats          产品统计
GET    /api/products/sales          销售记录
```

### 财务管理
```
GET    /api/finance/records         收支记录
POST   /api/finance/records         添加记录
GET    /api/finance/stats           财务统计
GET    /api/finance/sales           销售分析
GET    /api/finance/expenses        费用分析
GET    /api/finance/report          财务报表
```

### 仪表盘
```
GET    /api/dashboard/stats         核心指标
GET    /api/dashboard/charts        图表数据
GET    /api/dashboard/alerts        待办提醒
```

---

## 7. 前端页面结构

```
登录页
├── 仪表盘
│   ├── 核心指标卡片
│   ├── 数据趋势图表
│   └── 待办事项
├── 内容管理
│   ├── 栏目管理
│   └── 文章管理
│       ├── 文章列表
│       ├── 文章编辑
│       └── 审核管理（管理员）
├── 文件管理
│   └── 文件列表/上传
├── 用户管理
│   ├── 后台用户（管理员）
│   └── 注册用户
│       ├── 用户列表
│       └── 用户分析
├── 供应商管理
│   ├── 供应商列表
│   ├── 供应商详情
│   └── 供应商分析
├── 产品管理
│   ├── 产品分类
│   ├── 产品列表
│   └── 销售分析
├── 财务管理
│   ├── 收支记录
│   ├── 销售分析
│   ├── 费用分析
│   └── 财务报表
└── 系统设置（管理员）
    ├── 基础设置
    └── 操作日志
```

---

## 8. 部署方案

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=sqlite:///data/raocms.db
      - SECRET_KEY=your-secret-key
      
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

---

## 9. 开发阶段

### Phase 1 — 基础框架
- [x] 项目结构初始化
- [ ] 用户认证体系（多角色）
- [ ] 基础权限控制

### Phase 2 — 内容管理
- [ ] 栏目管理
- [ ] 文章管理（含审核流程）
- [ ] 文件管理

### Phase 3 — 业务模块
- [ ] 注册用户管理
- [ ] 供应商管理
- [ ] 产品管理

### Phase 4 — 财务分析
- [ ] 销售分析
- [ ] 费用分析
- [ ] 财务报表

### Phase 5 — 仪表盘
- [ ] 数据可视化
- [ ] 核心指标
- [ ] 待办提醒

---

*最后更新：2026-04-06*
