---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/ux-design-specification.md'
---

# RainClaw - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for RainClaw 数据源配置功能, decomposing the requirements from the PRD, UX Design, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: 管理员可以查看所有已配置的数据源列表
FR2: 管理员可以创建新的数据源配置
FR3: 管理员可以编辑已存在的数据源配置
FR4: 管理员可以删除已存在的数据源配置
FR5: 管理员可以为数据源设置唯一编码（code）
FR6: 系统将数据源配置持久化存储到 MongoDB
FR7: 系统支持 MySQL 类型的数据源配置
FR8: 系统支持 PostgreSQL 类型的数据源配置
FR9: 系统支持 Oracle 类型的数据源配置
FR10: 系统支持 MongoDB 类型的数据源配置
FR11: 系统支持 SQL Server 类型的数据源配置
FR12: 左侧菜单栏提供"数据源配置"入口
FR13: 菜单项仅管理员可见
FR14: 页面风格与现有平台一致
FR15: 列表支持按名称模糊查询

### NonFunctional Requirements

NFR1: 数据源管理页面仅管理员可访问
NFR2: API 接口需要 JWT 认证
NFR3: 数据库连接凭证以明文存储在 MongoDB
NFR4: 菜单样式与现有左侧菜单保持一致

### Additional Requirements

- AR1: 棕地项目，直接复用现有 FastAPI + MongoDB + Vue 3 架构
- AR2: RESTful API 路由 `/api/v1/datasources`
- AR3: MongoDB `datasources` 集合 + `code` 字段唯一索引
- AR4: 数据模型字段：name, code, host, port, database_name, username, password, db_type, created_at, updated_at
- AR5: 前端路由 `/chat/datasources` 子页面
- AR6: 统一响应格式 `{ code, msg, data }`
- AR7: 错误提示支持国际化（vue-i18n）
- AR8: 不分页，列表一次性加载

### UX Design Requirements

UX-DR1: 列表页表格展示所有数据源，列包含：名称、编码、类型、主机、端口、用户名、密码、操作
UX-DR2: 密码列默认显示 `***`，点击眼睛图标切换明文显示
UX-DR3: 列表上方提供名称搜索输入框 + 查询/重置按钮
UX-DR4: 新增/编辑使用 Modal 弹窗，不跳转页面
UX-DR5: 表单字段一行两个（grid 两列布局），包含：名称、编码、主机、端口、库名、账号、密码、数据库类型（下拉）
UX-DR6: 编辑时密码明文回显，无需重复填写
UX-DR7: 编码唯一性在提交时校验，前端展示对应错误提示
UX-DR8: 删除操作需二次确认（确认对话框）
UX-DR9: 空状态时显示"暂无数据源"提示
UX-DR10: 操作成功/失败使用 Toast 提示
UX-DR11: 使用现有 RainClaw 组件风格，不引入新 UI 框架

### FR Coverage Map

| FR | 归属 | 说明 |
|----|------|------|
| FR1 | Epic 1 - Stories 2, 3 | 查看数据源列表 |
| FR2 | Epic 1 - Stories 2, 3 | 创建数据源 |
| FR3 | Epic 1 - Stories 2, 3 | 编辑数据源 |
| FR4 | Epic 1 - Stories 2, 3 | 删除数据源 |
| FR5 | Epic 1 - Stories 1, 2 | 唯一编码 |
| FR6 | Epic 1 - Story 1 | MongoDB 持久化 |
| FR7-FR11 | Epic 1 - Stories 1, 2 | 5种数据库类型支持 |
| FR12 | Epic 1 - Story 4 | 左侧菜单入口 |
| FR13 | Epic 1 - Stories 2, 4 | 仅管理员可见 |
| FR14 | Epic 1 - Story 3 | 风格一致 |
| FR15 | Epic 1 - Stories 2, 3 | 按名称模糊查询 |

## Epic List

### Epic 1: 数据源配置管理

管理员可以通过 Web 界面完成数据源的增删改查管理，支持五种数据库类型的连接信息配置。

**FRs 覆盖：** FR1, FR2, FR3, FR4, FR5, FR6, FR7, FR8, FR9, FR10, FR11, FR12, FR13, FR14, FR15

**Story 规划：**
1. 后端数据模型 + MongoDB 集合（数据模型、索引）
2. 后端 CRUD API 路由（RESTful API、校验、权限）
3. 前端数据源管理页面（列表、Modal 表单、搜索、密码显隐）
4. 左侧菜单入口 + 国际化（菜单配置、i18n 文案）

### Story 1.1: 后端数据模型与 MongoDB 集合

As a **管理员**,
I want **系统能够存储数据源配置信息**,
So that **后续 CRUD 操作有数据基础**。

**Acceptance Criteria:**

**Given** 系统启动时
**When** 加载数据库配置
**Then** 自动创建 `datasources` 集合
**And** 在 `code` 字段上建立唯一索引

**Given** 数据源模型定义
**When** 查看 `models/datasource.py`
**Then** 包含字段：`name`, `code`, `host`, `port`, `database_name`, `username`, `password`, `db_type`, `created_at`, `updated_at`
**And** `db_type` 限定为 MySQL / PostgreSQL / Oracle / MongoDB / SQL Server

**FR 覆盖：** FR5, FR6, FR7, FR8, FR9, FR10, FR11
**涉及文件：** `backend/models/datasource.py`, `backend/mongodb/db.py`

### Story 1.2: 后端 CRUD API 路由

As a **管理员**,
I want **通过 RESTful API 对数据源进行增删改查**,
So that **前端页面可以调用接口完成管理操作**。

**Acceptance Criteria:**

**Given** 管理员已登录且拥有 admin 角色
**When** 发送 `GET /api/v1/datasources`
**Then** 返回所有数据源列表，格式为 `{ code: 0, msg: "success", data: [...] }`
**And** 支持 `?name=xxx` 参数进行模糊查询

**Given** 管理员已登录且拥有 admin 角色
**When** 发送 `POST /api/v1/datasources` 携带完整数据源信息
**Then** 返回 `{ code: 0, msg: "success", data: { ... } }`
**And** 若 `code` 已存在，返回 `{ code: 400, msg: "code already exists", data: null }`

**Given** 管理员已登录且拥有 admin 角色
**When** 发送 `PUT /api/v1/datasources/{id}` 携带更新字段
**Then** 更新成功返回 `{ code: 0, msg: "success", data: { ... } }`
**And** 若 ID 不存在，返回 `{ code: 404, msg: "not found", data: null }`

**Given** 管理员已登录且拥有 admin 角色
**When** 发送 `DELETE /api/v1/datasources/{id}`
**Then** 删除成功返回 `{ code: 0, msg: "success", data: null }`

**Given** 非管理员或无 JWT 令牌
**When** 访问任意数据源 API
**Then** 返回未授权错误（由现有 JWT 中间件处理）

**FR 覆盖：** FR1, FR2, FR3, FR4, FR5, FR13, FR15
**NFR 覆盖：** NFR1, NFR2
**涉及文件：** `backend/routers/datasources.py`, `backend/models/datasource.py`, `backend/main.py`

### Story 1.3: 前端数据源管理页面

As a **管理员**,
I want **通过 Web 界面查看、新增、编辑和删除数据源**,
So that **无需直接操作数据库即可管理数据源配置**。

**Acceptance Criteria:**

**Given** 管理员进入数据源管理页面
**When** 页面加载完成
**Then** 以表格形式展示所有数据源，列包含：名称、编码、类型、主机、端口、用户名、密码、操作
**And** 密码列默认显示 `***`，点击眼睛图标切换明文/掩码

**Given** 列表中无数据源
**When** 页面加载
**Then** 显示空状态提示"暂无数据源"

**Given** 管理员在搜索框输入名称关键字
**When** 点击"查询"按钮
**Then** 列表过滤显示名称匹配的数据源
**And** 点击"重置"按钮清空搜索条件，恢复全量列表

**Given** 管理员点击"新增数据源"按钮
**When** 弹出 Modal 表单
**Then** 表单字段一行两个排列，包含：名称、编码、主机、端口、库名、账号、密码、数据库类型（下拉）
**And** 编码字段提示"每个数据源的编码唯一，不可重复"

**Given** 管理员点击列表中某行的"编辑"
**When** 弹出 Modal 表单
**Then** 所有字段回填已有数据，密码明文回显

**Given** 管理员填写完表单后点击"保存"
**When** 编码已存在
**Then** 显示对应错误提示（国际化翻译）
**And** 保存成功时显示 Toast "保存成功"

**Given** 管理员点击某行的"删除"
**When** 弹出确认对话框
**Then** 确认后删除该数据源，显示 Toast "删除成功"

**FR 覆盖：** FR1, FR2, FR3, FR4, FR14, FR15
**UX-DR 覆盖：** UX-DR1, UX-DR2, UX-DR3, UX-DR4, UX-DR5, UX-DR6, UX-DR7, UX-DR8, UX-DR9, UX-DR10, UX-DR11
**涉及文件：** `frontend/src/pages/DatasourcesPage.vue`, `frontend/src/api/datasources.ts`

### Story 1.4: 左侧菜单入口 + 国际化

As a **管理员**,
I want **在左侧菜单看到"数据源配置"入口，且页面文案支持中英文**,
So that **我可以快速进入管理页面，界面语言与平台一致**。

**Acceptance Criteria:**

**Given** 管理员登录平台
**When** 查看左侧菜单
**Then** 显示"数据源配置"菜单项，风格与现有菜单项一致
**And** 点击后跳转到 `/chat/datasources` 页面

**Given** 非管理员用户登录平台
**When** 查看左侧菜单
**Then** 不显示"数据源配置"菜单项

**Given** 系统语言设置为中文
**When** 查看数据源管理页面
**Then** 所有文案（表格标题、表单标签、按钮、提示消息、错误信息）显示中文

**Given** 系统语言设置为英文
**When** 查看数据源管理页面
**Then** 所有文案显示英文

**FR 覆盖：** FR12, FR13, FR14
**NFR 覆盖：** NFR4
**涉及文件：** `frontend/src/main.ts`, `frontend/src/locales/zh.ts`, `frontend/src/locales/en.ts`
