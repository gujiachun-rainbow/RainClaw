from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import shortuuid

from backend.im.base import IMPlatform
from backend.mongodb.db import db


@dataclass
class IMUserBinding:
    id: str
    platform: IMPlatform
    platform_user_id: str
    platform_union_id: Optional[str]
    science_user_id: str
    created_at: int
    updated_at: int
    status: str = "active"


class IMUserBindingManager:
    def __init__(self):
        self.collection_name = "im_user_bindings"

    async def get_binding(self, platform: IMPlatform, platform_user_id: str) -> Optional[IMUserBinding]:
        doc = await db.get_collection(self.collection_name).find_one(
            {
                "platform": platform.value,
                "platform_user_id": platform_user_id,
                "status": "active",
            }
        )
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def get_binding_by_science_user(self, platform: IMPlatform, science_user_id: str) -> Optional[IMUserBinding]:
        doc = await db.get_collection(self.collection_name).find_one(
            {
                "platform": platform.value,
                "science_user_id": science_user_id,
                "status": "active",
            },
            sort=[("updated_at", -1)],
        )
        if not doc:
            return None
        return self._doc_to_model(doc)

    async def create_binding(
        self,
        platform: IMPlatform,
        platform_user_id: str,
        science_user_id: str,
        platform_union_id: Optional[str] = None,
    ) -> IMUserBinding:
        now = int(time.time())
        existing = await db.get_collection(self.collection_name).find_one(
            {
                "platform": platform.value,
                "platform_user_id": platform_user_id,
            }
        )
        if existing:
            await db.get_collection(self.collection_name).update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "science_user_id": science_user_id,
                        "platform_union_id": platform_union_id,
                        "updated_at": now,
                        "status": "active",
                    }
                },
            )
            updated = await db.get_collection(self.collection_name).find_one({"_id": existing["_id"]})
            return self._doc_to_model(updated)

        binding = IMUserBinding(
            id=shortuuid.uuid(),
            platform=platform,
            platform_user_id=platform_user_id,
            platform_union_id=platform_union_id,
            science_user_id=science_user_id,
            created_at=now,
            updated_at=now,
            status="active",
        )
        await db.get_collection(self.collection_name).insert_one(
            {
                "_id": binding.id,
                "platform": binding.platform.value,
                "platform_user_id": binding.platform_user_id,
                "platform_union_id": binding.platform_union_id,
                "science_user_id": binding.science_user_id,
                "created_at": binding.created_at,
                "updated_at": binding.updated_at,
                "status": binding.status,
            }
        )
        return binding

    async def remove_binding(self, platform: IMPlatform, platform_user_id: str) -> bool:
        result = await db.get_collection(self.collection_name).update_one(
            {
                "platform": platform.value,
                "platform_user_id": platform_user_id,
            },
            {"$set": {"status": "inactive", "updated_at": int(time.time())}},
        )
        return result.modified_count > 0

    async def remove_binding_by_science_user(self, platform: IMPlatform, science_user_id: str) -> bool:
        result = await db.get_collection(self.collection_name).update_many(
            {
                "platform": platform.value,
                "science_user_id": science_user_id,
                "status": "active",
            },
            {"$set": {"status": "inactive", "updated_at": int(time.time())}},
        )
        return result.modified_count > 0

    def _doc_to_model(self, doc: dict) -> IMUserBinding:
        return IMUserBinding(
            id=doc["_id"],
            platform=IMPlatform(doc["platform"]),
            platform_user_id=doc["platform_user_id"],
            platform_union_id=doc.get("platform_union_id"),
            science_user_id=doc["science_user_id"],
            created_at=int(doc.get("created_at", 0)),
            updated_at=int(doc.get("updated_at", 0)),
            status=doc.get("status", "active"),
        )
