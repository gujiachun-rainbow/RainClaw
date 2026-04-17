from __future__ import annotations

import time
import uuid
import secrets
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Response, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import bcrypt

from backend.mongodb.db import db
from backend.config import settings
from backend.user.dependencies import get_current_user, require_user, User

router = APIRouter(prefix="/auth", tags=["auth"])

class ApiResponse(BaseModel):
    code: int = Field(default=0, description="业务状态码，0 表示成功")
    msg: str = Field(default="ok", description="业务消息")
    data: Any = Field(default=None, description="返回数据")

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    fullname: str
    email: str
    password: str
    username: Optional[str] = None

class AuthUser(BaseModel):
    id: str
    fullname: str
    email: str
    role: str = "user"
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_login_at: Optional[str] = None

class AuthStatusData(BaseModel):
    authenticated: bool
    auth_provider: str = "local"
    user: Optional[AuthUser] = None


class TokenResponse(BaseModel):
    user: AuthUser
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ChangeFullnameRequest(BaseModel):
    fullname: str


def _user_doc_to_auth_user(doc: dict[str, Any]) -> AuthUser:
    created_at = doc.get("created_at")
    updated_at = doc.get("updated_at")
    last_login_at = doc.get("last_login_at")

    def _to_str_ts(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (int, float)):
            return datetime.fromtimestamp(int(v)).isoformat()
        return str(v)

    return AuthUser(
        id=str(doc.get("_id") or doc.get("id") or ""),
        fullname=str(doc.get("fullname") or doc.get("username") or ""),
        email=str(doc.get("email") or ""),
        role=str(doc.get("role") or "user"),
        is_active=bool(doc.get("is_active", True)),
        created_at=_to_str_ts(created_at),
        updated_at=_to_str_ts(updated_at),
        last_login_at=_to_str_ts(last_login_at) if last_login_at else None,
    )

@router.get("/check-default-password", response_model=ApiResponse)
async def check_default_password() -> ApiResponse:
    """Check whether the bootstrap admin account still uses the default password."""
    username = str(getattr(settings, "bootstrap_admin_username", "admin") or "admin").strip()
    default_pwd = str(getattr(settings, "bootstrap_admin_password", "admin123") or "admin123")

    user_doc = await db.get_collection("users").find_one({"username": username})
    if not user_doc:
        return ApiResponse(data={"is_default": False})

    stored_hash = user_doc.get("password_hash")
    if not stored_hash:
        return ApiResponse(data={"is_default": False})

    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")

    is_default = bcrypt.checkpw(default_pwd.encode("utf-8"), stored_hash)
    return ApiResponse(data={"is_default": is_default, "username": username, "password": default_pwd if is_default else None})


@router.post("/login", response_model=ApiResponse)
async def login(body: LoginRequest, response: Response):
    user_doc = await db.get_collection("users").find_one({"username": body.username})
    if not user_doc:
        return ApiResponse(code=401, msg="Invalid username or password")
    
    # Check password
    stored_hash = user_doc["password_hash"]
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
        
    if not bcrypt.checkpw(body.password.encode('utf-8'), stored_hash):
        return ApiResponse(code=401, msg="Invalid username or password")

    if not user_doc.get("is_active", True):
        return ApiResponse(code=403, msg="User is deactivated")

    # Create session tokens (access_token is a session id)
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(48)
    expires_at = int(time.time()) + settings.session_max_age
    refresh_expires_at = int(time.time()) + settings.session_max_age * 4
    
    await db.get_collection("user_sessions").insert_one({
        "_id": access_token,
        "user_id": str(user_doc["_id"]),
        "username": user_doc["username"],
        "role": user_doc.get("role", "user"),
        "created_at": int(time.time()),
        "expires_at": expires_at,
        "refresh_token": refresh_token,
        "refresh_expires_at": refresh_expires_at,
    })

    now = int(time.time())
    await db.get_collection("users").update_one(
        {"_id": str(user_doc["_id"])},
        {"$set": {"last_login_at": datetime.fromtimestamp(now).isoformat(), "updated_at": now}},
    )

    # Set cookie
    response.set_cookie(
        key=settings.session_cookie,
        value=access_token,
        max_age=settings.session_max_age,
        httponly=True,
        secure=settings.https_only,
        samesite="lax"
    )

    return ApiResponse(
        data=TokenResponse(
            user=_user_doc_to_auth_user(user_doc),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        ).model_dump()
    )

@router.post("/register", response_model=ApiResponse)
async def register(body: RegisterRequest):
    username = (body.username or body.email or "").strip()
    if not username:
        return ApiResponse(code=400, msg="Username/email required")

    existing = await db.get_collection("users").find_one({"username": username})
    if existing:
        return ApiResponse(code=400, msg="Username already exists")

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(body.password.encode('utf-8'), salt).decode('utf-8')
    
    user_id = str(uuid.uuid4())
    now = int(time.time())
    
    new_user = {
        "_id": user_id,
        "username": username,
        "password_hash": hashed,
        "fullname": body.fullname or username,
        "email": body.email,
        "role": "user",
        "is_active": True,
        "created_at": now,
        "updated_at": now,
        "last_login_at": None,
    }
    
    await db.get_collection("users").insert_one(new_user)

    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(48)
    expires_at = int(time.time()) + settings.session_max_age
    refresh_expires_at = int(time.time()) + settings.session_max_age * 4
    await db.get_collection("user_sessions").insert_one(
        {
            "_id": access_token,
            "user_id": user_id,
            "username": username,
            "role": "user",
            "created_at": int(time.time()),
            "expires_at": expires_at,
            "refresh_token": refresh_token,
            "refresh_expires_at": refresh_expires_at,
        }
    )

    return ApiResponse(
        data=TokenResponse(
            user=_user_doc_to_auth_user(new_user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
        ).model_dump()
    )

@router.get("/status", response_model=ApiResponse)
async def get_auth_status(current_user: Optional[User] = Depends(get_current_user)) -> ApiResponse:
    auth_provider = getattr(settings, "auth_provider", "local")
    if auth_provider == "none":
        return ApiResponse(
            data=AuthStatusData(
                authenticated=True,
                auth_provider="none",
                user=AuthUser(
                    id="anonymous",
                    fullname="Anonymous User",
                    email="anonymous@localhost",
                    role="user",
                    is_active=True,
                    created_at="",
                    updated_at="",
                    last_login_at=None,
                ),
            ).model_dump()
        )

    if not current_user:
        return ApiResponse(data=AuthStatusData(authenticated=False, auth_provider=auth_provider).model_dump())

    user_doc = await db.get_collection("users").find_one({"_id": str(current_user.id)})
    user = _user_doc_to_auth_user(user_doc or {"_id": current_user.id, "username": current_user.username, "email": "", "role": current_user.role})
    return ApiResponse(data=AuthStatusData(authenticated=True, auth_provider=auth_provider, user=user).model_dump())


@router.get("/me", response_model=ApiResponse)
async def me(current_user: User = Depends(require_user)) -> ApiResponse:
    user_doc = await db.get_collection("users").find_one({"_id": str(current_user.id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    return ApiResponse(data=_user_doc_to_auth_user(user_doc).model_dump())


@router.post("/refresh", response_model=ApiResponse)
async def refresh(body: RefreshTokenRequest) -> ApiResponse:
    doc = await db.get_collection("user_sessions").find_one({"refresh_token": body.refresh_token})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if int(doc.get("refresh_expires_at") or 0) < int(time.time()):
        await db.get_collection("user_sessions").delete_one({"_id": doc.get("_id")})
        raise HTTPException(status_code=401, detail="Refresh token expired")

    old_session_id = doc.get("_id")
    await db.get_collection("user_sessions").delete_one({"_id": old_session_id})

    access_token = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + settings.session_max_age
    await db.get_collection("user_sessions").insert_one(
        {
            "_id": access_token,
            "user_id": str(doc.get("user_id")),
            "username": str(doc.get("username")),
            "role": str(doc.get("role") or "user"),
            "created_at": int(time.time()),
            "expires_at": expires_at,
            "refresh_token": body.refresh_token,
            "refresh_expires_at": int(doc.get("refresh_expires_at") or 0),
        }
    )
    return ApiResponse(data=RefreshTokenResponse(access_token=access_token, token_type="Bearer").model_dump())


@router.post("/change-password", response_model=ApiResponse)
async def change_password(body: ChangePasswordRequest, current_user: User = Depends(require_user)) -> ApiResponse:
    user_doc = await db.get_collection("users").find_one({"_id": str(current_user.id)})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hash = user_doc.get("password_hash")
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode("utf-8")
    if not stored_hash or not bcrypt.checkpw(body.old_password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=400, detail="Invalid old password")

    hashed = bcrypt.hashpw(body.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    await db.get_collection("users").update_one(
        {"_id": str(current_user.id)},
        {"$set": {"password_hash": hashed, "updated_at": int(time.time())}},
    )
    return ApiResponse(data={"ok": True})


@router.post("/change-fullname", response_model=ApiResponse)
async def change_fullname(body: ChangeFullnameRequest, current_user: User = Depends(require_user)) -> ApiResponse:
    fullname = (body.fullname or "").strip()
    if not fullname:
        raise HTTPException(status_code=400, detail="fullname required")

    await db.get_collection("users").update_one(
        {"_id": str(current_user.id)},
        {"$set": {"fullname": fullname, "updated_at": int(time.time())}},
    )
    user_doc = await db.get_collection("users").find_one({"_id": str(current_user.id)})
    return ApiResponse(data=_user_doc_to_auth_user(user_doc or {"_id": current_user.id, "fullname": fullname, "email": "", "role": current_user.role}).model_dump())

@router.post("/logout", response_model=ApiResponse)
async def logout(request: Request, response: Response):
    session_id = request.cookies.get(settings.session_cookie)
    if session_id:
        await db.get_collection("user_sessions").delete_one({"_id": session_id})
    
    response.delete_cookie(settings.session_cookie)
    return ApiResponse(data={"ok": True})
