"""Webhook models for notification channels (Feishu, DingTalk, WeCom)."""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class WebhookCreate(BaseModel):
    name: str = Field(..., description="Webhook display name")
    type: str = Field(..., description="feishu | dingtalk | wecom")
    url: str = Field(..., description="Webhook URL")


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None


class WebhookOut(BaseModel):
    id: str
    name: str
    type: str
    url: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


WEBHOOK_TYPES = {"feishu", "dingtalk", "wecom"}


def webhook_doc_to_out(doc: Dict[str, Any]) -> WebhookOut:
    wid = doc.get("_id")
    if hasattr(wid, "hex"):
        wid = str(wid)
    return WebhookOut(
        id=str(wid),
        name=doc.get("name", ""),
        type=doc.get("type", "feishu"),
        url=doc.get("url", ""),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )
