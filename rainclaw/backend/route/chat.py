"""
Task-invoked chat API.

POST /api/v1/chat — 供任务调度服务调用，执行一次 LLM 对话并返回完整输出。
POST /api/v1/task/parse-schedule — 自然语言定时描述转 crontab（使用系统配置的大模型）。
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional

import shortuuid
from fastapi import APIRouter, Header, HTTPException
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field

from backend.config import settings
from backend.deepagent.engine import get_llm_model
from backend.deepagent.runner import arun_science_task_stream
from backend.deepagent.sessions import async_create_science_session
from backend.mongodb.db import db

router = APIRouter(tags=["chat"])


def _now_ts() -> int:
    return int(time.time())


def _new_event_id() -> str:
    return shortuuid.uuid()


def _wrap_event(event: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {"event": event, "data": data}


def _append_session_event(session: Any, event: Dict[str, Any]) -> None:
    events = getattr(session, "events", None)
    if not isinstance(events, list):
        events = []
        setattr(session, "events", events)
    events.append(event)
    if event.get("event") == "message":
        data = event.get("data") or {}
        content = data.get("content")
        if isinstance(content, str) and content.strip():
            setattr(session, "latest_message", content)
            setattr(session, "latest_message_at", int(data.get("timestamp") or _now_ts()))

# 定时描述转 crontab 的提示词（与 task-service 一致）
PARSE_SCHEDULE_SYSTEM = """You are a cron schedule assistant. You ONLY accept inputs that are a **complete, clear, and unambiguous** schedule or time description.

You MUST reply with INVALID if any of the following is true:
1. The input is NOT a schedule/time description (e.g. question "你是谁", greeting "你好").
2. The input is **incomplete** — sentence is cut off or missing words (e.g. "每5分钟执行一" missing "次").
3. The input is **ambiguous or unclear** — could mean more than one schedule, or the intended time is not clear.

When replying INVALID, you MUST output exactly 4 lines:
Line 1: the word INVALID
Line 2: the first suggested complete schedule description that the user most likely meant (infer from their input; e.g. for "每5分钟执行一" suggest "每5分钟执行一次")
Line 3: the second suggested schedule description (another reasonable completion or alternative)
Line 4: the third suggested schedule description (yet another alternative)

Each suggestion must be a complete, valid schedule phrase that can be converted to crontab. Output in the same language as the user's input (Chinese or English).

When the input IS a complete and clear schedule description, reply with exactly one line: the standard crontab expression (5 fields: minute hour day-of-month month day-of-week). No explanation, no markdown, no quotes.

Examples of valid inputs and outputs:
- "每天早上9点" -> 0 9 * * *
- "每5分钟执行一次" -> */5 * * * *
- "每周一10点" -> 0 10 * * 1
- "every day at 9am" -> 0 9 * * *

Reply with either (a) one crontab line, or (b) four lines: INVALID, suggestion1, suggestion2, suggestion3. Nothing else."""
CRONTAB_RE = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")

# 时间相关关键词，用于预检「明显不是定时描述」的输入
_SCHEDULE_KEYWORDS = re.compile(
    r"点|分[钟]?|时|每天|每[周月日时]|every|hour|minute|day|week|month|"
    r"morning|afternoon|noon|midnight|daily|weekly|monthly|cron|"
    r"早上|晚上|凌晨|上午|下午|星期|周一|周二|三|四|五|六|日|"
    r"\d{1,2}\s*[:：]\s*\d{1,2}|\d+\s*[点时分]",
    re.IGNORECASE,
)

def _looks_like_schedule(text: str) -> bool:
    """若文本中完全不含时间相关关键词，视为非定时描述。"""
    return bool(_SCHEDULE_KEYWORDS.search(text))


class TaskChatRequest(BaseModel):
    input: str = Field(..., description="Prompt input for LLM")
    source: str = Field(default="task", description="Must be 'task' for task invocation")
    task_id: Optional[str] = Field(default=None, description="Task ID for logging")
    user_id: Optional[str] = Field(default=None, description="Owner user_id so the created session appears in their Chats")
    model_config_id: Optional[str] = Field(default=None, description="Model config ID to use for this task")


async def _verify_task_api_key(x_api_key: Optional[str] = None) -> None:
    """If TASK_SERVICE_API_KEY is set, require it in X-API-Key header."""
    if not settings.task_service_api_key:
        return
    if (x_api_key or "").strip() != settings.task_service_api_key.strip():
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


@router.post("/chat")
async def task_chat(
    body: TaskChatRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Dict[str, Any]:
    """
    任务调度服务调用：创建临时会话，执行 LLM 对话，收集完整回复后返回。
    不返回 SSE 流，直接返回 JSON。
    """
    await _verify_task_api_key(x_api_key)
    if (body.source or "").strip() != "task":
        raise HTTPException(status_code=400, detail="source must be 'task'")
    prompt = (body.input or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="input is required")

    owner_user_id = (body.user_id or "").strip() or "task-system"
    model_config_dict = None
    if body.model_config_id:
        from backend.models import get_model_config
        mc = await get_model_config(body.model_config_id)
        if mc:
            model_config_dict = mc.model_dump()
    session = await async_create_science_session(
        mode="deep",
        user_id=owner_user_id,
        model_config=model_config_dict,
        source="task",
    )
    chat_id = session.session_id
    output = ""
    error_msg: Optional[str] = None
    ts = _now_ts()
    # 写入用户消息，便于会话在 Chats 列表中有完整对话记录
    user_event = _wrap_event("message", {
        "event_id": _new_event_id(),
        "timestamp": ts,
        "content": prompt,
        "role": "user",
        "attachments": [],
    })
    _append_session_event(session, user_event)
    await session.save()

    try:
        async for evt in arun_science_task_stream(session, prompt):
            event_type = evt.get("event") or ""
            data = evt.get("data") or {}
            if event_type == "planning_message":
                output = (data.get("content") or "").strip()
                break
            if event_type == "error":
                error_msg = data.get("message") or "Unknown error"
                break
        # 将会话状态与助手回复写入 DB，这样该会话会在 Chats 列表中显示并有标题/预览
        setattr(session, "status", "completed")
        if error_msg:
            err_evt = _wrap_event("error", {"event_id": _new_event_id(), "timestamp": _now_ts(), "error": error_msg})
            _append_session_event(session, err_evt)
            setattr(session, "latest_message", error_msg[:500] if len(error_msg) > 500 else error_msg)
            setattr(session, "latest_message_at", _now_ts())
        else:
            assist_evt = _wrap_event("message", {
                "event_id": _new_event_id(),
                "timestamp": _now_ts(),
                "content": output,
                "role": "assistant",
                "attachments": [],
            })
            _append_session_event(session, assist_evt)
        # 定时任务会话标题：用 prompt 前 50 字，避免空标题导致列表里难辨认
        if not (getattr(session, "title", None) or "").strip():
            title = (prompt[:50] + "…") if len(prompt) > 50 else prompt
            setattr(session, "title", title or "定时任务")
        # 开启分享，使 /share/{session_id} 可访问，执行详情里的「查看」链接与对话页分享按钮一致
        setattr(session, "is_shared", True)
        await session.save()
        if error_msg:
            return {"chat_id": chat_id, "output": "", "error": error_msg}
        return {"chat_id": chat_id, "output": output}
    except Exception as exc:
        logger.exception("task_chat failed")
        setattr(session, "status", "completed")
        err_evt = _wrap_event("error", {"event_id": _new_event_id(), "timestamp": _now_ts(), "error": str(exc)})
        _append_session_event(session, err_evt)
        setattr(session, "latest_message", str(exc)[:500])
        setattr(session, "latest_message_at", _now_ts())
        if not (getattr(session, "title", None) or "").strip():
            setattr(session, "title", "定时任务")
        setattr(session, "is_shared", True)
        await session.save()
        return {"chat_id": chat_id, "output": "", "error": str(exc)}


# ─── 定时描述转 crontab（使用系统配置的用户模型）────────────────────────────────────

class ParseScheduleRequest(BaseModel):
    schedule_desc: str = Field(..., description="自然语言定时描述")
    model_config_id: Optional[str] = Field(default=None, description="Model config ID to use for parsing")


async def _resolve_any_model_config() -> Optional[dict]:
    """找到任意一个可用的模型配置，供 get_llm_model 使用。

    优先使用 settings 中的全局默认（DeepSeek env），
    其次使用数据库中任意 active 且有 api_key 的模型。
    无可用模型时返回 None。
    """
    if (getattr(settings, "model_ds_api_key", None) or "").strip():
        return {"_use_default": True}
    doc = await db.get_collection("models").find_one(
        {"is_active": True, "api_key": {"$nin": ["", None]}},
        sort=[("created_at", -1)],
    )
    if doc:
        return {
            "model_name": doc.get("model_name"),
            "base_url": doc.get("base_url"),
            "api_key": doc.get("api_key"),
            "context_window": doc.get("context_window"),
        }
    return None


@router.post("/task/parse-schedule")
async def parse_schedule(
    body: ParseScheduleRequest,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> Dict[str, Any]:
    """
    将自然语言定时描述转为 crontab，使用系统配置的大模型（如 DeepSeek）。
    未配置大模型时返回 400，提示用户先在设置中配置。
    """
    await _verify_task_api_key(x_api_key)
    desc = (body.schedule_desc or "").strip()[:200]
    if not desc:
        raise HTTPException(status_code=400, detail="schedule_desc is required")

    # 预检：明显不是时间描述的输入直接拒绝，不调用 LLM，但仍返回默认建议
    if not _looks_like_schedule(desc):
        raise HTTPException(
            status_code=400,
            detail={
                "message": "描述不是有效的时间或定时说明，请选择或输入一个定时描述。",
                "suggestions": ["每天早上9点", "每周一上午10点", "每30分钟执行一次"],
            },
        )
    llm_config = None
    if body.model_config_id:
        from backend.models import get_model_config
        mc = await get_model_config(body.model_config_id)
        if mc:
            llm_config = mc.model_dump()
    if llm_config is None:
        model_cfg = await _resolve_any_model_config()
        if model_cfg is None:
            raise HTTPException(
                status_code=400,
                detail="请先在设置中配置大模型（API Key 与模型），再使用自然语言定时。",
            )
        llm_config = None if "_use_default" in model_cfg else model_cfg

    try:
        llm = get_llm_model(config=llm_config, max_tokens_override=200, streaming=False)
        response = await llm.ainvoke([
            SystemMessage(content=PARSE_SCHEDULE_SYSTEM),
            HumanMessage(content=desc),
        ])
        content = (response.content or "").strip()
        lines = [ln.strip().strip("'\"").strip() for ln in content.split("\n") if ln.strip()]
        first = (lines[0] if lines else "").strip()
        if first.upper() == "INVALID":
            suggestions = [ln for ln in lines[1:4] if ln and not ln.upper() == "INVALID"]
            detail_msg = "描述不完整或有歧义，请修改。"
            if suggestions:
                raise HTTPException(
                    status_code=400,
                    detail={"message": detail_msg, "suggestions": suggestions[:3]},
                )
            raise HTTPException(status_code=400, detail=detail_msg)
        if CRONTAB_RE.match(first):
            return {"crontab": first}
        raise HTTPException(
            status_code=400,
            detail="无法解析为有效的 crontab，请填写明确的时间描述，如「每天早上9点」。",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("parse_schedule failed")
        raise HTTPException(status_code=500, detail=str(exc))
