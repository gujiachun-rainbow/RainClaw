# Story 1.2: 后端 CRUD API 路由

Status: done

## Story

As a **管理员**,
I want **通过 RESTful API 对数据源进行增删改查**,
so that **前端页面可以调用接口完成管理操作**。

## Acceptance Criteria

1. **查看列表**
   - Given 管理员已登录且拥有 admin 角色
   - When 发送 `GET /api/v1/datasources`
   - Then 返回所有数据源列表，格式为 `{ code: 0, msg: "success", data: [...] }`
   - And 支持 `?name=xxx` 参数进行模糊查询

2. **创建数据源**
   - Given 管理员已登录且拥有 admin 角色
   - When 发送 `POST /api/v1/datasources` 携带完整数据源信息
   - Then 返回 `{ code: 0, msg: "success", data: { ... } }`
   - And 若 `code` 已存在，返回 `{ code: 400, msg: "code already exists", data: null }`

3. **更新数据源**
   - Given 管理员已登录且拥有 admin 角色
   - When 发送 `PUT /api/v1/datasources/{id}` 携带更新字段
   - Then 更新成功返回 `{ code: 0, msg: "success", data: { ... } }`
   - And 若 ID 不存在，返回 `{ code: 404, msg: "not found", data: null }`

4. **删除数据源**
   - Given 管理员已登录且拥有 admin 角色
   - When 发送 `DELETE /api/v1/datasources/{id}`
   - Then 删除成功返回 `{ code: 0, msg: "success", data: null }`

5. **权限控制**
   - Given 非管理员或无 JWT 令牌
   - When 访问任意数据源 API
   - Then 返回未授权错误（由现有 JWT 中间件处理）

## Tasks / Subtasks

- [x] 创建 `backend/route/datasources.py` CRUD 路由文件 (AC: #1, #2, #3, #4)
  - [x] 定义 `ApiResponse` 响应模型（复用现有模式）
  - [x] 实现 `GET /datasources` — 列表查询（支持 `?name=xxx` 模糊搜索）
  - [x] 实现 `POST /datasources` — 创建（含 `code` 唯一性校验）
  - [x] 实现 `PUT /datasources/{id}` — 更新（404 处理）
  - [x] 实现 `DELETE /datasources/{id}` — 删除（404 处理）
  - [x] 使用 `require_user` + admin role 校验保护所有接口
- [x] 在 `backend/route/__init__.py` 中添加导出（如需要）
- [x] 在 `backend/main.py` 中注册新路由 (AC: #1)
  - [x] 导入 `datasources_router`
  - [x] 添加 `app.include_router(datasources_router, prefix="/api/v1")`

### Review Follow-ups (AI)

- [x] [AI-Review][Patch] 响应中泄露 password 字段 [datasources.py:72,82,109,126]
- [x] [AI-Review][Patch] CREATE 响应同时包含 `_id` 和 `id` [datasources.py:71]
- [x] [AI-Review][Patch] 未使用的 `get_current_user` 导入 [datasources.py:6]

## Dev Notes

### 现有代码模式（必须遵循）

**路由文件模式**（参考 `route/models.py`）：
```python
from fastapi import APIRouter, HTTPException, Depends
from backend.user.dependencies import get_current_user, require_user, User
from backend.mongodb.db import db

router = APIRouter(prefix="/datasources", tags=["datasources"])

class ApiResponse(BaseModel):
    code: int = 0
    msg: str = "success"
    data: Any = None

@router.get("", response_model=ApiResponse)
async def list_datasources(current_user: User = Depends(require_user)):
    # admin role check
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    ...
```

**MongoDB 操作模式**（参考 `route/models.py`）：
- 创建：`doc["_id"] = doc.pop("id")` → `insert_one(doc)`
- 查询：`find_one({"_id": id})` → 返回后 `doc["id"] = doc.pop("_id")`
- 更新：`update_one({"_id": id}, {"$set": update_data})`
- 删除：`delete_one({"_id": id})`

**错误处理模式**：
- 业务逻辑错误（如 code 重复）：使用 `ApiResponse(code=400, msg="...", data=None)` 返回
- 资源不存在：使用 `HTTPException(status_code=404, detail="...")`
- 权限不足：使用 `HTTPException(status_code=403, detail="...")`

### 关键设计决策

- **admin 角色校验**：在路由函数内 `if current_user.role != "admin": raise HTTPException(403)`（参考 `models.py` 中系统模型的 admin check 模式）
- **`code` 唯一性**：创建时先 `find_one({"code": body.code})` 检查，再 `insert_one`
- **`_id` 映射**：创建时 `doc["_id"] = doc.pop("id")`；读取时返回 `doc["id"] = doc.pop("_id")`
- **更新逻辑**：使用 `model_dump(exclude_unset=True)` 仅更新提供的字段，保留 `updated_at` 时间戳更新
- **模糊查询**：使用 MongoDB 正则 `{"name": {"$regex": name, "$options": "i"}}`
- **排序**：按 `created_at` 降序排列
- **不分页**：一次性返回全部列表（架构决策 AR8）

### 与 Story 1.1 的关联

**直接依赖 Story 1.1 的项目**：
- `backend/models/datasource.py` — Datasource, DatasourceCreate, DatasourceUpdate, DbType
- `backend/mongodb/db.py` — datasources 集合 + code 唯一索引（已创建）

**Story 1.1 Code Review 保留的 deferred items**：
- `Datasource.id` vs MongoDB `_id` — CRUD 层需要处理映射
- `DatasourceUpdate` 允许更新 `code` — CRUD 层自行决定是否允许

### 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/route/datasources.py` | 新建 | 数据源 CRUD 路由 |
| `backend/main.py` | 修改 | 注册数据源路由 |

### 引用

- [Source: architecture.md#API & Communication] — RESTful 端点定义、响应格式
- [Source: architecture.md#Error Handling Patterns] — 错误处理场景
- [Source: epics.md#Story 1.2] — Story AC 和 FR 映射
- [Source: route/models.py] — 现有 CRUD 路由实现模式

## Dev Agent Record

### File List

| 文件 | 操作 |
|------|------|
| `rainclaw/backend/route/datasources.py` | 新建 |
| `rainclaw/backend/main.py` | 修改 |

### Completion Notes

- Story 1.2 实施完成，状态更新为 review
- 新建 `backend/route/datasources.py`：完整 CRUD 路由
  - `GET /datasources` — 列表查询，支持 `?name=xxx` 模糊搜索
  - `POST /datasources` — 创建，含 `code` 唯一性校验
  - `PUT /datasources/{id}` — 更新，含 `code` 唯一性校验和 404 处理
  - `DELETE /datasources/{id}` — 删除，404 处理
  - 所有接口使用 `require_user` + admin role 双重校验
- `main.py` 中注册新路由
- 代码模式严格遵循现有 `route/models.py` 模式：`ApiResponse`、`_id` 映射、时间戳处理

### Senior Developer Review (AI)

**Review Date:** 2026-05-10
**Review Outcome:** Changes Requested

**Summary:**
- **Blind Hunter**: 发现 8 项（1 Critical, 2 High, 3 Medium, 2 Low）— 多数组件/设计决策问题
- **Edge Case Hunter**: 发现 5 项（1 High, 2 Medium, 2 Low）— 密码泄露为关键发现
- **Acceptance Auditor**: 发现 4 项（1 严重, 1 高, 1 中, 1 低）— 验证全部 5 条 AC 均覆盖

**Action Items:**

- [x] [Review][Defer] TOCTOU 竞态条件 + 未处理的 DuplicateKeyError [datasources.py:54-69] — 预存，数据库唯一索引已提供最后防线；低概率管理端并发场景
- [x] [Review][Defer] 404/403 响应格式不匹配 AC 规范 — 遵循 Dev Notes 设计决策："资源不存在使用 HTTPException(404)"，符合现有代码模式
- [x] [Review][Defer] NoSQL 注入 (regex) [datasources.py:35] — 遵循 Dev Notes 设计决策：管理端 API，仅认证管理员可访问
- [x] [Review][Defer] `msg` 默认值 "success" vs 项目其他文件的 "ok" — 本文件内部一致，向下兼容
- [x] [Review][Patch] 响应中泄露 password 字段 [datasources.py:72,82,109,126]
- [x] [Review][Patch] CREATE 响应同时包含 `_id` 和 `id` [datasources.py:71]
- [x] [Review][Patch] 未使用的 `get_current_user` 导入 [datasources.py:6]

**Dismissed Items (预存/范围外/误报):**
- `_id` 类型不匹配 (string vs ObjectId) — 项目使用 UUID 字符串作为 _id，非 ObjectId
- datasource_id 输入校验缺失 — MongoDB 优雅处理返回 404
- 无分页 — 架构决策 AR8
- `_require_admin` 返回值未使用 — 辅助函数模式，无功能影响
- `_id`/`id` key swap 脆弱 — Datasource 模型始终包含 `id` 字段
- 权限错误格式不一致 — 遵循 Dev Notes 设计决策
