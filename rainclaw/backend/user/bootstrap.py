from __future__ import annotations

import time
import uuid

import bcrypt
from loguru import logger

from backend.config import settings
from backend.mongodb.db import db


async def ensure_admin_user() -> None:
    if not getattr(settings, "bootstrap_admin_enabled", True):
        return

    username = str(getattr(settings, "bootstrap_admin_username", "admin") or "admin").strip()
    password = str(getattr(settings, "bootstrap_admin_password", "admin123") or "admin123")
    fullname = str(getattr(settings, "bootstrap_admin_fullname", "Administrator") or "Administrator")
    email = str(getattr(settings, "bootstrap_admin_email", "admin@localhost") or "admin@localhost")

    if not username:
        return

    users = db.get_collection("users")
    existing = await users.find_one({"username": username})
    now = int(time.time())

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    if not existing:
        user_id = str(uuid.uuid4())
        await users.insert_one(
            {
                "_id": user_id,
                "username": username,
                "password_hash": hashed,
                "fullname": fullname,
                "email": email,
                "role": "admin",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
                "last_login_at": None,
            }
        )
        logger.info("Bootstrapped admin user: {}", username)
        return

    if getattr(settings, "bootstrap_update_admin_password", False):
        await users.update_one(
            {"_id": existing.get("_id")},
            {
                "$set": {
                    "password_hash": hashed,
                    "fullname": fullname,
                    "email": email,
                    "role": existing.get("role") or "admin",
                    "is_active": existing.get("is_active", True),
                    "updated_at": now,
                }
            },
        )
        logger.info("Updated bootstrapped admin user password: {}", username)

