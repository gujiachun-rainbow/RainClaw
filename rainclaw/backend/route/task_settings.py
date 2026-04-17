from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.user.dependencies import require_user, User
from backend.task_settings import (
    TaskSettings,
    UpdateTaskSettingsRequest,
    get_task_settings,
    update_task_settings,
)

router = APIRouter(prefix="/task-settings", tags=["task-settings"])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


@router.get("", response_model=ApiResponse)
async def get_settings(current_user: User = Depends(require_user)):
    settings = await get_task_settings(current_user.id)
    return ApiResponse(data=settings.model_dump())


@router.put("", response_model=ApiResponse)
async def update_settings(
    body: UpdateTaskSettingsRequest,
    current_user: User = Depends(require_user),
):
    settings = await update_task_settings(current_user.id, body)
    return ApiResponse(data=settings.model_dump())
