"""用户全局记忆（AGENTS.md）读写接口。"""

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.user.dependencies import require_user, User

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
