"""Webhook CRUD and test API."""
from datetime import datetime, timezone
from typing import Any, Dict, List

import shortuuid
from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from app.core.db import db
from app.models.webhook import (
    WEBHOOK_TYPES,
    WebhookCreate,
    WebhookOut,
    WebhookUpdate,
    webhook_doc_to_out,
)
from app.services.webhook_sender import send_test_message

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookOut)
async def create_webhook(body: WebhookCreate) -> WebhookOut:
    if body.type not in WEBHOOK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(sorted(WEBHOOK_TYPES))}")
    if not body.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")
    now = datetime.now(timezone.utc)
    wid = shortuuid.uuid()
    doc: Dict[str, Any] = {
        "_id": wid,
        "name": body.name.strip(),
        "type": body.type,
        "url": body.url.strip(),
        "created_at": now,
        "updated_at": now,
    }
    await db.get_collection("webhooks").insert_one(doc)
    logger.info(f"Webhook created: {wid} type={body.type}")
    return webhook_doc_to_out(doc)


@router.get("", response_model=List[WebhookOut])
async def list_webhooks() -> List[WebhookOut]:
    cursor = db.get_collection("webhooks").find({}).sort("created_at", -1)
    return [webhook_doc_to_out(d) async for d in cursor]


@router.get("/{webhook_id}", response_model=WebhookOut)
async def get_webhook(webhook_id: str) -> WebhookOut:
    doc = await db.get_collection("webhooks").find_one({"_id": webhook_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook_doc_to_out(doc)


@router.put("/{webhook_id}", response_model=WebhookOut)
async def update_webhook(webhook_id: str, body: WebhookUpdate) -> WebhookOut:
    doc = await db.get_collection("webhooks").find_one({"_id": webhook_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Webhook not found")
    update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        update["name"] = body.name.strip()
    if body.type is not None:
        if body.type not in WEBHOOK_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid type. Must be one of: {', '.join(sorted(WEBHOOK_TYPES))}")
        update["type"] = body.type
    if body.url is not None:
        if not body.url.strip():
            raise HTTPException(status_code=400, detail="URL is required")
        update["url"] = body.url.strip()
    await db.get_collection("webhooks").update_one({"_id": webhook_id}, {"$set": update})
    doc = await db.get_collection("webhooks").find_one({"_id": webhook_id})
    return webhook_doc_to_out(doc)


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str) -> None:
    res = await db.get_collection("webhooks").delete_one({"_id": webhook_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Webhook not found")
    await db.get_collection("tasks").update_many(
        {"webhook_ids": webhook_id},
        {"$pull": {"webhook_ids": webhook_id}},
    )
    logger.info(f"Webhook deleted: {webhook_id}, cleaned from tasks")


class TestWebhookBody(BaseModel):
    webhook_id: str = ""
    webhook_name: str = ""


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: str) -> dict:
    doc = await db.get_collection("webhooks").find_one({"_id": webhook_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Webhook not found")
    ok, message = await send_test_message(
        webhook_type=doc.get("type", "feishu"),
        webhook_url=doc.get("url", ""),
        webhook_name=doc.get("name", ""),
    )
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}
