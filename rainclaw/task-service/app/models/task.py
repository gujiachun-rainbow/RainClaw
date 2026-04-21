"""Task and task_run models."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_serializer


# ─── API schemas ───────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    name: str = Field(..., description="Task name")
    prompt: str = Field(..., description="Prompt input for LLM")
    schedule_desc: str = Field(..., description="Natural language schedule description")
    crontab: Optional[str] = Field(None, description="Crontab expression (auto-filled from schedule_desc if not set)")
    webhook: Optional[str] = Field(None, description="Legacy single Feishu webhook URL")
    webhook_ids: Optional[List[str]] = Field(default_factory=list, description="Managed webhook IDs")
    event_config: Optional[List[str]] = Field(default_factory=list, description="Events to notify")
    model_config_id: Optional[str] = Field(None, description="Model config ID for this task")
    status: str = Field(default="enabled", description="enabled | disabled")
    user_id: Optional[str] = Field(None, description="Owner user_id so task-run sessions appear in their Chats")


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    schedule_desc: Optional[str] = None
    crontab: Optional[str] = None
    webhook: Optional[str] = None
    webhook_ids: Optional[List[str]] = None
    event_config: Optional[List[str]] = None
    model_config_id: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    name: str
    prompt: str
    schedule_desc: str
    crontab: str
    webhook: Optional[str] = None
    webhook_ids: List[str] = Field(default_factory=list)
    event_config: List[str] = Field(default_factory=list)
    model_config_id: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    next_run: Optional[str] = Field(None, description="下次执行时间（展示时区）")
    total_runs: int = Field(0, description="累计执行次数")
    success_runs: int = Field(0, description="成功执行次数")
    success_rate: str = Field("", description="成功率（如 95%）")
    recent_runs: List[str] = Field(default_factory=list, description="最近7次执行状态")


class TaskRunOut(BaseModel):
    id: str
    task_id: str
    status: str  # success | failed
    chat_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[str] = None
    error: Optional[str] = None

    @field_serializer("start_time", "end_time")
    def _serialize_datetime_utc(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")


class TaskRunsPage(BaseModel):
    items: List[TaskRunOut] = Field(default_factory=list)
    total: int = Field(..., description="Total count of runs for the task")


# ─── Internal (Mongo) ────────────────────────────────────────────────────────

def task_doc_to_out(doc: Dict[str, Any]) -> TaskOut:
    tid = doc.get("_id")
    if hasattr(tid, "hex"):
        tid = str(tid)
    return TaskOut(
        id=str(tid),
        name=doc.get("name", ""),
        prompt=doc.get("prompt", ""),
        schedule_desc=doc.get("schedule_desc", ""),
        crontab=doc.get("crontab", ""),
        webhook=doc.get("webhook"),
        webhook_ids=doc.get("webhook_ids") or [],
        event_config=doc.get("event_config") or [],
        model_config_id=doc.get("model_config_id"),
        status=doc.get("status", "enabled"),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )


def task_run_doc_to_out(doc: Dict[str, Any]) -> TaskRunOut:
    rid = doc.get("_id")
    if hasattr(rid, "hex"):
        rid = str(rid)
    return TaskRunOut(
        id=str(rid),
        task_id=doc.get("task_id", ""),
        status=doc.get("status", "failed"),
        chat_id=doc.get("chat_id"),
        start_time=doc.get("start_time"),
        end_time=doc.get("end_time"),
        result=doc.get("result"),
        error=doc.get("error"),
    )
