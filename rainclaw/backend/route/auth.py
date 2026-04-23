from __future__ import annotations

import time
import uuid
import secrets
import random
from typing import Any, Optional
from datetime import datetime

from fastapi import APIRouter, Response, Request, HTTPException, Depends
from pydantic import BaseModel, Field
import bcrypt
import redis

from backend.mongodb.db import db
from backend.config import settings
from backend.user.dependencies import get_current_user, require_user, User

# SMTP邮件发送功能
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Redis连接
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    password=settings.redis_password,
    db=settings.redis_db,
    decode_responses=True
)

async def send_email(to: str, subject: str, body: str):
    """发送邮件"""
    # 从配置中获取SMTP设置
    smtp_server = getattr(settings, "smtp_server", "smtp.gmail.com")
    smtp_port = getattr(settings, "smtp_port", 465)
    smtp_username = getattr(settings, "smtp_username", "")
    smtp_password = getattr(settings, "smtp_password", "")
    smtp_from_email = getattr(settings, "smtp_from_email", smtp_username)
    
    if not smtp_username or not smtp_password:
        return {"success": False, "error": "SMTP configuration not set"}
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg["From"] = smtp_from_email
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        # 连接SMTP服务器并发送邮件
        if smtp_port == 465:
            # 使用SSL
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            # 使用TLS
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        return {"success": True, "message": f"Email sent successfully to {to}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
    verification_code: str

class SendVerificationCodeRequest(BaseModel):
    email: str
    purpose: str = "register"  # register or reset_password

class ResetPasswordRequest(BaseModel):
    email: str
    verification_code: str
    new_password: str

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

@router.post("/send-verification-code", response_model=ApiResponse)
async def send_verification_code(body: SendVerificationCodeRequest):
    email = body.email.strip()
    if not email:
        return ApiResponse(code=400, msg="Email required")

    # 检查邮箱是否已存在，根据目的不同逻辑不同
    existing = await db.get_collection("users").find_one({"email": email})
    if body.purpose == "register":
        if existing:
            return ApiResponse(code=400, msg="Email already registered")
    elif body.purpose == "reset_password":
        if not existing:
            return ApiResponse(code=400, msg="Email not found")

    # 生成6位数验证码
    code = ''.join(random.choices('0123456789', k=6))
    expires_at = int(time.time()) + 300  # 5分钟过期

    # 存储验证码到Redis，包含目的
    redis_key = f"verification_code:{email}:{body.purpose}"
    redis_client.setex(
        redis_key,
        300,  # 5分钟过期
        code
    )

    # 发送验证码邮件
    if body.purpose == "register":
        subject = "RainClaw 注册验证码"
        body_content = f"您的注册验证码是：{code}，有效期5分钟。请勿向他人泄露此验证码。"
    else:
        subject = "RainClaw 重置密码验证码"
        body_content = f"您的重置密码验证码是：{code}，有效期5分钟。请勿向他人泄露此验证码。"
    result = await send_email(
        to=email,
        subject=subject,
        body=body_content
    )

    if not result.get("success"):
        return ApiResponse(code=500, msg="Failed to send verification code")

    return ApiResponse(msg="Verification code sent successfully")

@router.post("/register", response_model=ApiResponse)
async def register(body: RegisterRequest):
    username = (body.username or body.email or "").strip()
    if not username:
        return ApiResponse(code=400, msg="Username/email required")

    # 检查邮箱唯一性
    existing_email = await db.get_collection("users").find_one({"email": body.email})
    if existing_email:
        return ApiResponse(code=400, msg="Email already registered")

    # 检查用户名唯一性
    existing_username = await db.get_collection("users").find_one({"username": username})
    if existing_username:
        return ApiResponse(code=400, msg="Username already exists")

    # 验证验证码
    redis_key = f"verification_code:{body.email}:register"
    stored_code = redis_client.get(redis_key)
    if not stored_code:
        return ApiResponse(code=400, msg="Verification code not found or expired")
    if stored_code != body.verification_code:
        return ApiResponse(code=400, msg="Invalid verification code")

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

    # 删除使用过的验证码
    redis_key = f"verification_code:{body.email}:register"
    redis_client.delete(redis_key)

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


@router.post("/reset-password", response_model=ApiResponse)
async def reset_password(body: ResetPasswordRequest):
    email = body.email.strip()
    verification_code = body.verification_code.strip()
    new_password = body.new_password.strip()

    if not email or not verification_code or not new_password:
        return ApiResponse(code=400, msg="Email, verification code and new password are required")

    # 验证验证码
    redis_key = f"verification_code:{email}:reset_password"
    stored_code = redis_client.get(redis_key)
    if not stored_code:
        return ApiResponse(code=401, msg="Invalid or expired verification code")

    if stored_code != verification_code:
        return ApiResponse(code=401, msg="Invalid verification code")

    # 检查用户是否存在
    user_doc = await db.get_collection("users").find_one({"email": email})
    if not user_doc:
        return ApiResponse(code=404, msg="User not found")

    # 哈希新密码
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # 更新密码
    await db.get_collection("users").update_one(
        {"_id": str(user_doc["_id"])},
        {"$set": {"password_hash": hashed, "updated_at": int(time.time())}},
    )

    # 删除使用过的验证码
    redis_client.delete(redis_key)

    return ApiResponse(msg="Password reset successfully")

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
