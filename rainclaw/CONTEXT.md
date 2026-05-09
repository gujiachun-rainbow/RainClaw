# RainClaw 领域上下文

## 项目定位
面向企业内部的通用 AI Agent 平台。

## 核心概念

### User（用户）
企业内部员工，通过邮箱注册，bcrypt 密码认证。有 `role` 属性（`user` / `admin`），但目前无实质权限区分，预留未来管理功能。

### Session（会话）
用户与 AI Agent 之间的一次对话。历史遗留名称为 `ScienceSession`，需统一为 `Session`。当前 `mode` 固定为 `"deep"`。

### Agent Instance（执行体）
在 Session 边界内执行 AI 推理的瞬态实例。每次对话请求时重建。Agent Instance ≠ Session：Session 是持久化的上下文边界，Agent Instance 是瞬态的。

### Agent Template / Agent 智能体（规划中）
可配置、可复用的 AI 工作者实体。用户可自定义：
- 名称和描述
- 系统提示词
- 关联的 Skills 和 Tools
- 独立的记忆上下文

用户创建 Session 时可以选择一个 Agent Template。一个智能体可对应多个 Session。（当前未实现）

### Channel（渠道）
用户与 Agent 交互的入口方式，同一个 User 可在不同渠道使用，但会话各自独立（不共享聊天记录）。
- **Web UI**（Vue 3 前端）：直接使用 sessions 集合
- **IM（即时通讯）**：通过 `im_chat_sessions` 表映射到 ScienceSession，通过 `im_user_bindings` 表将 IM 用户 ID 绑定到平台 User ID
  - 飞书（Lark OAPI 长连接）
  - 微信桥接

### Skill（技能）
"教 Agent 怎么做事"— 存放在技能目录下的指令集（提示词 + 逻辑模板），本质是文本文件。Agent 通过文件系统读取并遵循其指令。分两类：
- **内置 Skills**（`/builtin-skills/`）：随镜像内置，只读，不可修改（如 find-skills, skill-creator）
- **外置 Skills**（`/skills/`）：用户通过 find-skills 下载或自行安装，支持屏蔽和删除管理

### Tool（工具）
"让 Agent 能做事" — 可调用的 Python 函数，Agent 可以在推理过程中实际执行。分三类：
- **内置工具**：`web_search`, `web_crawl`, `propose_skill_save` 等 deepagent tools 模块中的函数
- **外部扩展工具**：`Tools/` 目录自动扫描加载的 Python 扩展
- **MCP 沙箱工具**：通过 MCP 协议在隔离沙箱中执行

### 层级关系
Agent → 读 Skills（学习怎么做）→ 调用 Tools（实际执行）

### Task（定时任务）
让 Agent 定时自动执行分析任务（如每天汇总数据生成报告推送到飞书群）。使用 Celery 调度，支持自然语言转 Crontab。

### Memory（记忆）
用户级别的全局记忆，以 `AGENTS.md` 文件存储在 `_memory/{user_id}/` 目录。内容注入所有 Session 的系统提示词中。支持 UI 手动编辑和 Agent 自动写入。

**规划中的改进**：
- 管理员可维护结构化记忆，存入 MongoDB
- 全局共享记忆（所有用户生效）
- 按用户隔离的记忆（替代当前文件系统方案）

### File（文件）
通过 Docker 共享卷（`workspace/`）在 backend 和 sandbox 之间同步。两种典型场景：
- 用户上传文件 → Agent 在沙箱中分析 → 返回结果
- Agent 在沙箱中生成文件 → 用户下载/预览

### Model（模型）
LLM 模型配置，用户私有（各自创建各自可见）。Session 中可随时切换模型。支持的提供商：DeepSeek, OpenAI, Anthropic, Gemini, GLM, Qwen, Kimi, MiniMax, Taichu

## 技术栈
- 后端：Python 3.12, FastAPI, LangChain, DeepAgents
- 前端：Vue 3, TypeScript, Vite, Tailwind CSS
- 数据库：MongoDB, Redis
- 任务调度：Celery, Croniter
- 搜索：SearXNG, Crawl4AI
- 沙箱：MCP 协议（防止 Agent 执行危险命令）
