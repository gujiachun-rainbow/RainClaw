from __future__ import annotations

import re
from typing import Optional

from backend.im.base import IMPlatform
from backend.im.user_binding import IMUserBinding, IMUserBindingManager

_LARK_BIND_COMMAND_RE = re.compile(r"^/bind_lark\s+([A-Za-z0-9_-]+)$", re.IGNORECASE)
_LARK_OPEN_ID_RE = re.compile(r"^ou_[A-Za-z0-9_-]+$")


class IMUserBindingService:
    def __init__(self, binding_repo: Optional[IMUserBindingManager] = None):
        self.binding_repo = binding_repo or IMUserBindingManager()

    def normalize_lark_user_id(self, raw_user_input: str) -> str:
        user_input = (raw_user_input or "").strip().strip("`")
        if not user_input:
            raise ValueError("飞书用户 ID 不能为空")

        bind_command_match = _LARK_BIND_COMMAND_RE.match(user_input)
        if bind_command_match:
            user_input = bind_command_match.group(1)

        if not _LARK_OPEN_ID_RE.match(user_input):
            raise ValueError("请输入飞书 open_id，或粘贴机器人返回的 /bind_lark ou_xxx 配对命令")
        return user_input

    async def bind_lark_user(
        self,
        science_user_id: str,
        raw_lark_user_id: str,
        lark_union_id: Optional[str] = None,
    ) -> IMUserBinding:
        lark_user_id = self.normalize_lark_user_id(raw_lark_user_id)
        return await self.binding_repo.create_binding(
            platform=IMPlatform.LARK,
            platform_user_id=lark_user_id,
            platform_union_id=lark_union_id,
            science_user_id=science_user_id,
        )

    async def get_lark_binding_status(self, science_user_id: str) -> Optional[IMUserBinding]:
        return await self.binding_repo.get_binding_by_science_user(
            platform=IMPlatform.LARK,
            science_user_id=science_user_id,
        )

    async def unbind_lark_user(self, science_user_id: str) -> bool:
        return await self.binding_repo.remove_binding_by_science_user(
            platform=IMPlatform.LARK,
            science_user_id=science_user_id,
        )
