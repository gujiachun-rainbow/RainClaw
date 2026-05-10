# Story 1.1: 后端数据模型与 MongoDB 集合

Status: done

## Story

As a **管理员**,
I want **系统能够存储数据源配置信息**,
so that **后续 CRUD 操作有数据基础**。

## Acceptance Criteria

1. **数据集合自动创建**
   - Given 系统启动时
   - When MongoDB 初始化索引
   - Then 自动创建 `datasources` 集合
   - And 在 `code` 字段上建立唯一索引

2. **数据模型定义完整**
   - Given 数据源模型已定义
   - When 导入 `Datasource` 模型
   - Then 包含以下字段：
     - `id: str` — UUID 主键
     - `name: str` — 数据源名称
     - `code: str` — 唯一编码标识
     - `host: str` — 主机地址/IP
     - `port: int` — 端口号
     - `database_name: str` — 数据库名
     - `username: str` — 登录账号
     - `password: str` — 登录密码
     - `db_type: str` — 数据库类型，限定枚举值
     - `created_at: int` — Unix 时间戳
     - `updated_at: int` — Unix 时间戳

3. **数据库类型枚举**
   - Given `db_type` 字段
   - When 设置值
   - Then 仅接受：`MySQL`, `PostgreSQL`, `Oracle`, `MongoDB`, `SQL Server`
   - And 传入非法值时抛出验证错误

4. **创建/更新请求模型**
   - Given 存在 `DatasourceCreate` 和 `DatasourceUpdate` 请求模型
   - When 创建时，所有必填字段不为空
   - Then 模型验证通过
   - When 更新时，所有字段可选
   - Then 仅更新提供的字段

## Tasks / Subtasks

- [x] 将 `backend/models.py` 转换为 `backend/models/__init__.py`（包结构） (AC: #2)
  - [x] 创建 `backend/models/` 目录
  - [x] 将 `models.py` 内容移至 `models/__init__.py`
  - [x] 验证所有现有导入路径 `from backend.models import ...` 正常工作
- [x] 创建 `backend/models/datasource.py` 数据模型文件 (AC: #2, #3)
  - [x] 定义 `Datasource` Pydantic 模型
  - [x] 定义 `DatasourceCreate` 请求模型（含必填校验）
  - [x] 定义 `DatasourceUpdate` 请求模型（全部可选）
  - [x] 定义 `DbType` 枚举类（5 种数据库类型）
  - [x] 使用 `uuid4` 生成 ID，`int(time.time())` 生成时间戳
- [x] 在 `backend/mongodb/db.py` 中添加 datasources 索引 (AC: #1)
  - [x] 在 `init_indexes()` 中添加 `datasources` 集合的 `code` 唯一索引

## Dev Notes

### 现有代码模式（必须遵循）

**Pydantic 模型模式**（参考 `models.py` 中 `ModelConfig`）：
```python
from pydantic import BaseModel, Field
import uuid
import time

class ExampleModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
```

**MongoDB 索引模式**（参考 `db.py` 中 `init_indexes()`）：
```python
await cls.db.datasources.create_index("code", unique=True)
```

**导入模式**：
```python
from backend.mongodb.db import db
```

### 包结构转换说明

当前 `backend/models.py` 是单文件，需转换为包结构：
1. 创建 `backend/models/` 目录
2. 将 `models.py` 重命名为 `models/__init__.py`
3. 所有 `from backend.models import ...` 的导入自动兼容（因为 `__init__.py` 暴露了原有内容）
4. 新增 `backend/models/datasource.py`

### 关键设计决策

- `db_type` 使用 Python `enum.Enum` + Pydantic 验证，而非数据库层面的 ENUM 类型
- `password` 明文字段，不做加密存储（按 NFR3 要求）
- `code` 唯一索引保证业务层面编码不重复
- 使用 Unix 时间戳（int）而非 datetime，与现有 `models.py` 模式一致

### 涉及文件

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/models.py` → `backend/models/__init__.py` | 重构 | 转换为包结构 |
| `backend/models/datasource.py` | 新建 | 数据源模型定义 |
| `backend/mongodb/db.py` | 修改 | 添加 datasources 索引 |

### 引用

- [Source: architecture.md#Data Architecture] — MongoDB 集合、字段定义、唯一索引
- [Source: architecture.md#Naming Patterns] — snake_case 命名规则
- [Source: architecture.md#Error Handling Patterns] — 错误响应格式
- [Source: epics.md#Story 1.1] — Story AC 和 FR 映射

## Dev Agent Record

### File List

| 文件 | 操作 |
|------|------|
| `rainclaw/backend/models.py` | 删除（迁移至包结构） |
| `rainclaw/backend/models/__init__.py` | 新建（原 models.py 内容） |
| `rainclaw/backend/models/datasource.py` | 新建 |
| `rainclaw/backend/mongodb/db.py` | 修改 |

### Completion Notes

- Story 1.1 实施完成，状态更新为 review
- `models.py` 转换为 `models/` 包结构（`__init__.py` 保留原导出，向后兼容）
- 新建 `models/datasource.py`：Datasource, DatasourceCreate, DatasourceUpdate, DbType
- `db.py` 添加了 `datasources` 集合的 `code` 唯一索引
- 所有 6 处 `from backend.models import ...` 导入路径兼容
- 语法验证全部通过
- Code Review 后修复了 3 个 patch 项：包级重新导出、端口范围校验、code 长度校验
- 新增 `deferred-work.md` 记录 6 项预存/设计决策问题

### Code Review (AI)

**Review Date:** 2026-05-10
**Review Outcome:** Approve with Minor Patches

**Summary:**
- **Blind Hunter**: 发现 14 项（2 Critical, 3 High, 7 Medium, 2 Low) — 多数为预存/范围外问题
- **Edge Case Hunter**: 发现 6 项（1 High, 2 Medium, 2 Low, 1 Info）
- **Acceptance Auditor**: 全部 4 条 AC 均满足，发现 2 项不符合既有模式

**Patch Items (Story 1.1 直接相关，需修复):**

- [x] `datasource.py` 未从 `__init__.py` 重新导出 [models/__init__.py] — 已添加 `from backend.models.datasource import ...`
- [x] `Datasource.port` 缺少端口范围校验 [models/datasource.py:21,34,45] — 已添加 `gt=0, lt=65536`
- [x] `Datasource.code` 缺少最小长度/格式校验 [models/datasource.py:18] — 已添加 `min_length=1`

**Deferred Items (预存/设计决策):**

- [x] [Review][Defer] 未使用的 `datetime` 导入（`__init__.py:3`）— pre-existing from original `models.py`
- [x] [Review][Defer] `time.time()` 返回 float 标注为 int — 与现有 `ModelConfig` 模式一致
- [x] [Review][Defer] `Datasource.id` vs MongoDB `_id` 映射 — consistent with existing `ModelConfig` pattern
- [x] [Review][Defer] `SQL Server` 带空格枚举值 — intentional per AC #3
- [x] [Review][Defer] `DatasourceUpdate` 允许更新 `code` — design decision, CRUD 层可处理
- [x] [Review][Defer] `Datasource` 密码明文存储 — documented design decision per NFR3

**Dismissed Items (预存/范围外):**

- `init_system_models` 无条件删除 system-qwen — 预存代码，非本 Story 引入
- `list_user_models` API Key 泄露 — 预存问题
- Datasource 缺少用户所有权 — 管理端全局功能设计
- SSL/TLS 连接配置缺失 — 范围外
- 竞态条件、`_id` 类型不一致、`context_window` 校验 — 均为预存代码问题

**Resolution:**
- 0 decision-needed, **3 patch**, 6 deferred, 7 dismissed as noise
