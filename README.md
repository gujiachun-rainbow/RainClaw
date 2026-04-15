# RainClaw

RainClaw 是一个强大的智能代理系统，旨在帮助用户解决问题、进行研究和高效完成任务。它基于先进的 LLM 技术，支持多种模型，并提供了丰富的技能和工具扩展系统。

## 项目结构

```
RainClaw/
├── Skills/              # 技能模块目录
│   ├── brainstorming/   # 头脑风暴技能
│   ├── copywriting/     # 文案写作技能
│   ├── deep-research/   # 深度研究技能
│   ├── github-trending/ # GitHub 趋势技能
│   ├── read-github/     # GitHub 读取技能
│   ├── smtp-email/      # 邮件发送技能
│   ├── weather/         # 天气查询技能
│   └── writing-plans/   # 计划写作技能
├── Tools/               # 工具扩展目录
│   ├── __init__.py
│   └── query_weather.py # 天气查询工具
├── rainclaw/            # 核心代码目录
│   ├── backend/         # 后端代码
│   │   ├── deepagent/   # 深度代理实现
│   │   ├── mongodb/     # MongoDB 连接
│   │   ├── config.py    # 配置文件
│   │   └── pyproject.toml # 项目依赖
├── .gitignore           # Git 忽略文件
├── AGENTS.md            # 代理配置文件
├── LICENSE              # 许可证文件
└── README.md            # 项目说明文件
```

## 核心功能

- **多模型支持**：支持 OpenAI、Google Gemini、Anthropic Claude 等多种 LLM 模型
- **技能系统**：内置多种技能，如深度研究、文案写作、头脑风暴等
- **工具扩展**：支持自定义工具扩展，实现功能增强
- **沙箱执行**：安全的代码执行环境，隔离执行风险
- **实时信息**：集成网络搜索功能，获取最新信息
- **记忆系统**：跨会话记忆和会话级上下文管理
- **多语言支持**：支持中文和英文响应

## 技术栈

- **后端**：Python 3.12+
- **Web 框架**：FastAPI
- **异步服务器**：Uvicorn
- **数据验证**：Pydantic
- **数据库**：MongoDB (Motor 异步驱动)
- **LLM 集成**：LangChain、DeepAgents
- **事件流**：SSE (Server-Sent Events)
- **容器化**：Docker

## 依赖项

主要依赖项包括：

- fastapi==0.135.3
- uvicorn[standard]==0.44.0
- pydantic==2.13.0
- pydantic-settings==2.13.1
- python-dotenv==1.2.2
- sse-starlette==3.3.4
- loguru==0.7.3
- python-json-logger==4.1.0
- bcrypt==5.0.0
- shortuuid==1.0.13
- motor==3.7.1
- httpx==0.28.1
- tavily-python==0.7.23
- pyyaml==6.0.3
- deepagents==0.5.2
- langchain-mcp-adapters==0.2.2
- lark-oapi==1.5.3
- qrcode==8.2.0
- langchain==1.2.15
- langgraph==1.1.6
- langchain-community==0.4.1
- langchain-openai==1.1.13

## 安装指南

1. **克隆项目**

```bash
git clone https://github.com/yourusername/RainClaw.git
cd RainClaw
```

2. **创建虚拟环境**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **安装依赖**

```bash
cd rainclaw/backend
pip install -e .
```

4. **配置环境变量**

创建 `.env` 文件，添加以下配置：

```env
# 模型配置
MODEL_DS_NAME=gpt-4o
MODEL_DS_BASE_URL=https://api.openai.com/v1
MODEL_DS_API_KEY=your_api_key

# 数据库配置
MONGODB_URL=mongodb://localhost:27017

# 应用配置
CONTEXT_WINDOW=128000
MAX_TOKENS=4096
```

5. **启动服务**

```bash
uvicorn main:app --reload
```

## 技能系统

RainClaw 包含以下内置技能：

- **brainstorming**：头脑风暴，用于创意生成和问题解决
- **copywriting**：文案写作，用于生成营销文案和内容
- **deep-research**：深度研究，用于复杂主题的调研和分析
- **github-trending**：GitHub 趋势，获取热门开源项目
- **read-github**：读取 GitHub 仓库内容
- **smtp-email**：邮件发送，通过 SMTP 发送电子邮件
- **weather**：天气查询，获取实时天气信息
- **writing-plans**：计划写作，生成项目计划和任务列表

## 工具系统

RainClaw 支持以下内置工具：

- **web_search**：网络搜索，获取最新信息
- **web_crawl**：网页爬取，获取网页内容
- **propose_skill_save**：保存新技能
- **propose_tool_save**：保存新工具
- **eval_skill**：评估技能性能
- **grade_eval**：评估结果评分

## 工作流程

1. **理解与计划**：分析用户需求，制定执行计划
2. **执行**：使用技能或工具完成任务
3. **验证与交付**：检查任务完成情况，交付结果
4. **反思与捕获**：总结经验，更新记忆系统

## 记忆系统

RainClaw 采用两层记忆系统：

- **全局记忆** (AGENTS.md)：存储用户偏好和通用模式，跨所有会话持久化
- **会话记忆** (CONTEXT.md)：存储当前项目/任务上下文，会话结束后自动清理

## 配置说明

### 模型配置

- `MODEL_DS_NAME`：模型名称，如 gpt-4o、claude-3-opus 等
- `MODEL_DS_BASE_URL`：模型 API 基础 URL
- `MODEL_DS_API_KEY`：模型 API 密钥
- `CONTEXT_WINDOW`：模型上下文窗口大小

### 应用配置

- `MAX_TOKENS`：模型最大输出 tokens
- `SANDBOX_EXEC_TIMEOUT`：沙箱执行超时时间
- `MAX_OUTPUT_CHARS`：最大输出字符数

## 贡献指南

1. ** Fork 项目**
2. **创建功能分支**
3. **提交更改**
4. **创建 Pull Request**

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 鸣谢

- [LangChain](https://www.langchain.com/)：LLM 应用开发框架
- [DeepAgents](https://github.com/deepagents-ai/deepagents)：深度代理系统
- [FastAPI](https://fastapi.tiangolo.com/)：现代 Web 框架

---

**RainClaw** - 您的智能任务助手，让复杂任务变得简单！