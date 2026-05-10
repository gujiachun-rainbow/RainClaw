---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish']
releaseMode: single-release
inputDocuments: []
workflowType: 'prd'
documentCounts:
  brief: 0
  research: 0
  brainstorming: 0
  projectDocs: 0
classification:
  projectType: web_app
  domain: general
  complexity: low
  projectContext: brownfield
---

# Product Requirements Document - RainClaw

**Author:** 老GO
**Date:** 2026-05-09

## Executive Summary

RainClaw 平台数据库源配置功能，为管理员提供 Web 界面管理 MySQL、PostgreSQL、Oracle、MongoDB、SQL Server 五种数据库的连接信息。数据源配置以场景标签（tag）分类，持久化存储在 MongoDB 中，供后续 AI Agent 按场景自动连接查询。

**本次范围：** 数据源配置的 Web CRUD 管理，不含 AI Agent 集成（后续处理）。

**目标用户：** 平台管理员。

### What Makes This Special

将数据库连接抽象为一次配置、持续复用的基础能力：
- **声明式管理：** Web 界面声明数据源，非对话中临时描述
- **多库支持：** 统一管理多种关系型和非关系型数据库
- **场景编码：** 按业务场景给数据源分配唯一编码，为后续 Agent 自动匹配做准备

### Project Classification

- **项目类型：** Web App — RainClaw 平台内的管理功能
- **领域：** 通用基础设施
- **复杂度：** 低
- **项目状态：** 棕地开发 — 基于现有 FastAPI + Vue 3 架构扩展

## Success Criteria

### User Success
- 管理员通过 Web 界面完成数据源 CRUD，配置项含名称、编码、主机、端口、库名、账号、密码、数据库类型
- 管理员可为数据源打标签，区分不同业务场景

### Technical Success
- 支持五种数据库类型配置
- 连接凭证明文存储在 MongoDB
- 后端 API 仅管理员可访问

## Product Scope

### MVP - Minimum Viable Product
- Web 界面数据源 CRUD
- 五种数据库类型支持
- 左侧菜单"数据源配置"入口（仅管理员可见，风格与平台一致）
- 场景编码（唯一标识）

## User Journeys

### Journey 1: 管理员配置数据源

管理员登录 RainClaw 平台，进入数据源管理页面，填写名称、编码、主机、端口、库名、账号、密码、数据库类型后保存。支持后续编辑、删除、查看。

### Journey Requirements Summary
- 数据源 CRUD 管理页面
- 管理员权限控制
- 场景标签分类

## Web App Specific Requirements

### Technical Architecture Considerations
- **前端：** 现有 Vue 3 + TypeScript + Tailwind CSS 新增管理页面
- **后端：** 现有 FastAPI 新增 `/api/v1/datasources` 路由
- **数据存储：** 现有 MongoDB 新建 `datasources` 集合
- **身份认证：** 复用现有 JWT 认证中间件
- **路由：** 在现有 `/chat` 路由体系下新增子页面

### Implementation Considerations
- 表单字段：名称、编码、主机、端口、库名、账号、密码、数据库类型（下拉）
- 列表展示所有数据源，支持编辑和删除

## Functional Requirements

### 数据源管理
- FR1: 管理员可以查看所有已配置的数据源列表
- FR2: 管理员可以创建新的数据源配置
- FR3: 管理员可以编辑已存在的数据源配置
- FR4: 管理员可以删除已存在的数据源配置
- FR5: 管理员可以为数据源设置唯一编码（code）
- FR6: 系统将数据源配置持久化存储到 MongoDB

### 数据库类型支持
- FR7: 系统支持 MySQL 类型的数据源配置
- FR8: 系统支持 PostgreSQL 类型的数据源配置
- FR9: 系统支持 Oracle 类型的数据源配置
- FR10: 系统支持 MongoDB 类型的数据源配置
- FR11: 系统支持 SQL Server 类型的数据源配置

### 前端展示
- FR12: 左侧菜单栏提供"数据源配置"入口
- FR13: 菜单项仅管理员可见
- FR14: 页面风格与现有平台一致
- FR15: 列表支持按名称模糊查询

### 后续处理（本次不开发）
- AI Agent 通过 Tools 获取数据源信息
- Agent 根据场景编码自动匹配并连接数据源

## Non-Functional Requirements

### Security
- NFR1: 数据源管理页面仅管理员可访问
- NFR2: API 接口需要 JWT 认证
- NFR3: 数据库连接凭证以明文存储在 MongoDB

### Compatibility
- NFR4: 菜单样式与现有左侧菜单保持一致
