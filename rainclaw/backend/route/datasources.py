from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import time

from backend.user.dependencies import require_user, User
from backend.mongodb.db import db
from backend.models.datasource import Datasource, DatasourceCreate, DatasourceUpdate

router = APIRouter(prefix="/datasources", tags=["datasources"])


class ApiResponse(BaseModel):
    code: int = 0
    msg: str = "success"
    data: Any = None


def _require_admin(user: User) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("", response_model=ApiResponse)
async def list_datasources(
    name: Optional[str] = Query(None, description="按名称模糊查询"),
    current_user: User = Depends(require_user),
):
    """获取数据源列表，支持按名称模糊查询"""
    _require_admin(current_user)

    query = {}
    if name:
        query["name"] = {"$regex": name, "$options": "i"}

    cursor = db.get_collection("datasources").find(query).sort("created_at", -1)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(doc)

    return ApiResponse(data=results)


@router.post("", response_model=ApiResponse)
async def create_datasource(
    body: DatasourceCreate,
    current_user: User = Depends(require_user),
):
    """创建新的数据源"""
    _require_admin(current_user)

    # Check code uniqueness
    existing = await db.get_collection("datasources").find_one({"code": body.code})
    if existing:
        return ApiResponse(code=400, msg="code already exists", data=None)

    now = int(time.time())
    datasource = Datasource(
        **body.model_dump(),
        created_at=now,
        updated_at=now,
    )

    doc = datasource.model_dump()
    doc["_id"] = doc.pop("id")

    await db.get_collection("datasources").insert_one(doc)

    doc["id"] = str(doc.pop("_id"))
    return ApiResponse(data=doc)


@router.put("/{datasource_id}", response_model=ApiResponse)
async def update_datasource(
    datasource_id: str,
    body: DatasourceUpdate,
    current_user: User = Depends(require_user),
):
    """更新数据源"""
    _require_admin(current_user)

    existing = await db.get_collection("datasources").find_one({"_id": datasource_id})
    if not existing:
        raise HTTPException(status_code=404, detail="not found")

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        existing["id"] = str(existing.pop("_id"))
        return ApiResponse(data=existing)

    # If code is being updated, check uniqueness
    if "code" in update_data:
        dup = await db.get_collection("datasources").find_one(
            {"code": update_data["code"], "_id": {"$ne": datasource_id}}
        )
        if dup:
            return ApiResponse(code=400, msg="code already exists", data=None)

    update_data["updated_at"] = int(time.time())

    await db.get_collection("datasources").update_one(
        {"_id": datasource_id},
        {"$set": update_data},
    )

    updated = await db.get_collection("datasources").find_one({"_id": datasource_id})
    updated["id"] = str(updated.pop("_id"))
    return ApiResponse(data=updated)


@router.delete("/{datasource_id}", response_model=ApiResponse)
async def delete_datasource(
    datasource_id: str,
    current_user: User = Depends(require_user),
):
    """删除数据源"""
    _require_admin(current_user)

    existing = await db.get_collection("datasources").find_one({"_id": datasource_id})
    if not existing:
        raise HTTPException(status_code=404, detail="not found")

    await db.get_collection("datasources").delete_one({"_id": datasource_id})
    return ApiResponse(data=None)
