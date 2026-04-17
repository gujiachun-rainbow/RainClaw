from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import time
from loguru import logger

from backend.mongodb.db import db
from backend.config import settings

class ModelConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Display Name")
    provider: str = Field(..., description="openai, anthropic, etc.")
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: str = Field(..., description="Actual model name e.g. gpt-4o")
    context_window: Optional[int] = Field(
        default=None,
        description="Model context window in tokens. Auto-detected from model_name if not set.",
    )
    is_system: bool = False
    user_id: Optional[str] = None
    is_active: bool = True
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))

class CreateModelRequest(BaseModel):
    name: str
    provider: str = "openai"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: str
    context_window: Optional[int] = Field(
        default=None,
        ge=1024, le=10_000_000,
        description="Model context window in tokens. Leave empty for auto-detection.",
    )

class UpdateModelRequest(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    context_window: Optional[int] = Field(
        default=None,
        ge=1024, le=10_000_000,
        description="Model context window in tokens. Leave empty for auto-detection.",
    )
    is_active: Optional[bool] = None

async def init_system_models():
    """
    Initialize system models from environment variables or settings.
    Only creates system model when DS_API_KEY is configured;
    otherwise cleans up any existing system model with empty key.
    """
    now = int(time.time())

    await db.get_collection("models").delete_one({"_id": "system-qwen", "is_system": True})

    if not settings.model_ds_api_key:
        await db.get_collection("models").delete_one({"_id": "system-default", "is_system": True})
        logger.info("DS_API_KEY not set, skipping system model creation")
        return

    system_definitions = [
        {
            "_id": "system-default",
            "name": "DeepSeek V3.2",
            "provider": "deepseek",
            "base_url": settings.model_ds_base_url,
            "api_key": settings.model_ds_api_key,
            "model_name": settings.model_ds_name,
            "context_window": settings.context_window,
            "is_system": True,
            "is_active": True,
        }
    ]

    for doc in system_definitions:
        existing = await db.get_collection("models").find_one({"_id": doc["_id"]})
        doc = {**doc, "updated_at": now}
        if not existing:
            doc["created_at"] = now
            await db.get_collection("models").insert_one(doc)
        else:
            await db.get_collection("models").update_one({"_id": doc["_id"]}, {"$set": doc})

async def get_model_config(model_id: str) -> Optional[ModelConfig]:
    doc = await db.get_collection("models").find_one({"_id": model_id})
    if not doc:
        return None
    # Remap _id to id
    doc["id"] = doc["_id"]
    return ModelConfig(**doc)

async def list_user_models(user_id: str) -> List[ModelConfig]:
    # Return System models + User models
    cursor = db.get_collection("models").find({
        "$or": [
            {"is_system": True},
            {"user_id": user_id}
        ]
    }).sort("created_at", -1)
    
    models = []
    async for doc in cursor:
        doc["id"] = doc["_id"]
        models.append(ModelConfig(**doc))
    return models
