# Deferred Work

## Deferred from: code review of 1-1-后端数据模型与-mongodb-集合 (2026-05-10)

- Unused `datetime` import in `rainclaw/backend/models/__init__.py:3` — pre-existing issue from original `models.py`, not introduced by this story
- `Datasource.id` vs MongoDB `_id` mapping — consistent with existing `ModelConfig` pattern, handled at CRUD layer (Story 1.2)
- `SQL Server` space in enum value — intentional per AC #3 specification

## Deferred from: code review of 1-2-后端-crud-api-路由 (2026-05-10)

- TOCTOU 竞态条件 + 未处理的 DuplicateKeyError on `code` uniqueness — 数据库唯一索引已提供最后防线；低概率管理端并发场景
- 404/403 响应格式不匹配 AC 规范 (`{code,msg,data}` vs FastAPI `HTTPException`) — 遵循 Dev Notes 设计决策，与现有代码模式保持一致
- NoSQL 注入风险 (regex in `list_datasources`) — 遵循 Dev Notes 设计决策，管理端 API 仅认证管理员可访问
- `msg` 默认值不一致 ("success" vs 项目其他文件的 "ok") — 本文件内部一致，向前兼容

## Deferred from: code review of 1-3-前端数据源管理页面 (2026-05-10)

- `loadList()` 竞态条件 — 管理端低并发场景概率极低
- `toSnakeCase` 连续大写字母处理（如 `SQLServer` → `s_q_l_server`）— 当前字段名全部转换正确，仅潜在的 future-proof 问题
- 硬编码 CSS 颜色值 — 遵循现有项目模式，非本变更引入
- 路由冲突 / LeftPanel 未排除 datasources 路径 — Story 1.4 左侧菜单入口将统一处理导航和高亮
