# Task Scheduler Service

独立部署的任务调度服务，与主聊天服务通过 API 交互。支持自然语言定时规则、Celery 调度、调用聊天接口执行 LLM 任务、飞书 Webhook 推送与执行历史。

## 功能

- **任务管理**: 创建 / 列表 / 更新 / 删除任务
- **定时规则**: 自然语言描述（如「每天早上9点」）经 LLM 转为 crontab
- **Celery Beat**: 每分钟检查到期任务并触发执行
- **执行流程**: 调用主服务 `POST /api/v1/chat` 执行任务，记录 `task_runs`，成功后推送飞书

## 环境变量

| 变量 | 说明 |
|------|------|
| MONGODB_HOST / MONGODB_PORT / MONGODB_DB / MONGODB_USER / MONGODB_PASSWORD | MongoDB 连接 |
| REDIS_URL | Celery broker（如 `redis://redis:6379/0`） |
| CHAT_SERVICE_URL | 主聊天服务地址（如 `http://backend:8000`） |
| CHAT_SERVICE_API_KEY | 调用主服务 `/api/v1/chat` 时使用的 API Key（需与主服务 TASK_SERVICE_API_KEY 一致） |
| DS_API_KEY / DS_URL / DS_MODEL | 自然语言转 crontab 时使用的 LLM |

## API

- `POST /tasks` — 创建任务
- `GET /tasks` — 任务列表
- `GET /tasks/{id}` — 任务详情
- `PUT /tasks/{id}` — 更新任务
- `DELETE /tasks/{id}` — 删除任务
- `GET /tasks/{id}/runs` — 执行历史

## 本地运行

```bash
cd rainclaw/task-service
pip install -r requirements.txt
# 设置环境变量后：
uvicorn app.main:app --host 0.0.0.0 --port 8001
# 另开终端：
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

## Docker Compose

与主项目一起编排时，会启动 `scheduler_api`、`celery_worker`、`celery_beat` 和 `redis`。主服务需配置 `TASK_SERVICE_API_KEY`，任务服务配置相同值到 `CHAT_SERVICE_API_KEY` 以调用主服务聊天接口。
