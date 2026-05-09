"""用户全局记忆（AGENTS.md）读写接口 + 管理员结构化记忆（MongoDB）CRUD。"""

import os
import time
from typing import Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from bson import ObjectId

from backend.user.dependencies import require_user, User
from backend.mongodb.db import db

router = APIRouter(prefix="/memory", tags=["memory"])

_WORKSPACE_DIR = os.environ.get("WORKSPACE_DIR", "/home/rainclaw")

_DEFAULT_CONTENT = (
    "# Global Memory (persists across all sessions)\n\n"
    "## User Preferences\n\n"
    "## General Patterns\n\n"
    "## Notes\n"
)


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


class UpdateMemoryRequest(BaseModel):
    content: str


def _memory_path(user_id: str) -> str:
    return os.path.join(_WORKSPACE_DIR, "_memory", user_id, "AGENTS.md")


@router.get("", response_model=ApiResponse)
async def get_memory(current_user: User = Depends(require_user)):
    path = _memory_path(current_user.id)
    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    else:
        content = _DEFAULT_CONTENT
    return ApiResponse(data={"content": content})


@router.put("", response_model=ApiResponse)
async def update_memory(
    body: UpdateMemoryRequest,
    current_user: User = Depends(require_user),
):
    path = _memory_path(current_user.id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(body.content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ApiResponse(data={"content": body.content})


# ═══════════════════════════════════════════════════════════════════
# 管理员结构化记忆 CRUD（MongoDB）
# ═══════════════════════════════════════════════════════════════════

class AdminMemoryEntry(BaseModel):
    """管理记忆条目"""
    id: str = Field(default="", description="MongoDB _id 字符串")
    scope: Optional[List[str]] = Field(
        default=None,
        description="null=全局可见, [uid1,uid2]=仅指定用户可见",
    )
    category: str = Field(default="preferences", description="preferences|patterns|notes|custom")
    content: str = Field(default="", description="记忆内容")
    created_by: str = Field(default="", description="创建者用户 ID")
    created_at: int = Field(default=0)
    updated_at: int = Field(default=0)


class CreateAdminMemoryRequest(BaseModel):
    scope: Optional[List[str]] = Field(default=None)
    category: str = Field(default="preferences")
    content: str = Field(default="")


class UpdateAdminMemoryRequest(BaseModel):
    scope: Optional[List[str]] = None
    category: Optional[str] = None
    content: Optional[str] = None


_MEMORY_COLLECTION = "memory_entries"


def _doc_to_entry(doc: dict) -> dict:
    """MongoDB 文档转前端友好格式。"""
    return {
        "id": str(doc["_id"]),
        "scope": doc.get("scope"),
        "category": doc.get("category", "preferences"),
        "content": doc.get("content", ""),
        "created_by": doc.get("created_by", ""),
        "created_at": doc.get("created_at", 0),
        "updated_at": doc.get("updated_at", 0),
    }


@router.get("/admin", response_model=ApiResponse)
async def list_admin_memory(current_user: User = Depends(require_user)):
    """列出所有记忆条目。scope=null 为全局条目。"""
    try:
        col = db.get_collection(_MEMORY_COLLECTION)
        cursor = col.find().sort("updated_at", -1)
        entries = []
        async for doc in cursor:
            entries.append(_doc_to_entry(doc))
        return ApiResponse(data={"entries": entries})
    except Exception as exc:
        logger.exception("list_admin_memory failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/admin", response_model=ApiResponse)
async def create_admin_memory(
    body: CreateAdminMemoryRequest,
    current_user: User = Depends(require_user),
):
    """创建一条记忆条目。"""
    try:
        now = int(time.time())
        doc = {
            "scope": body.scope,
            "category": body.category or "preferences",
            "content": body.content,
            "created_by": current_user.id,
            "created_at": now,
            "updated_at": now,
        }
        result = await db.get_collection(_MEMORY_COLLECTION).insert_one(doc)
        doc["_id"] = result.inserted_id
        return ApiResponse(data={"entry": _doc_to_entry(doc)})
    except Exception as exc:
        logger.exception("create_admin_memory failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.put("/admin/{entry_id}", response_model=ApiResponse)
async def update_admin_memory(
    entry_id: str,
    body: UpdateAdminMemoryRequest,
    current_user: User = Depends(require_user),
):
    """更新一条记忆条目。"""
    try:
        oid = ObjectId(entry_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid entry ID")

    try:
        update = {"updated_at": int(time.time())}
        if body.scope is not None:
            update["scope"] = body.scope
        if body.category is not None:
            update["category"] = body.category
        if body.content is not None:
            update["content"] = body.content

        result = await db.get_collection(_MEMORY_COLLECTION).update_one(
            {"_id": oid}, {"$set": update},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")

        doc = await db.get_collection(_MEMORY_COLLECTION).find_one({"_id": oid})
        return ApiResponse(data={"entry": _doc_to_entry(doc)})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("update_admin_memory failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/admin/{entry_id}", response_model=ApiResponse)
async def delete_admin_memory(
    entry_id: str,
    current_user: User = Depends(require_user),
):
    """删除一条记忆条目。"""
    try:
        oid = ObjectId(entry_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid entry ID")

    try:
        result = await db.get_collection(_MEMORY_COLLECTION).delete_one({"_id": oid})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        return ApiResponse(data={"ok": True})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("delete_admin_memory failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
