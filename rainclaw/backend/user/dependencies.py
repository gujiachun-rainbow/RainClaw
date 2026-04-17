from typing import Optional
from fastapi import Request, HTTPException, Depends
from pydantic import BaseModel
from backend.mongodb.db import db
from backend.config import settings

class User(BaseModel):
    id: str
    username: str
    role: str = "user"
    
async def get_current_user(request: Request) -> Optional[User]:
    """
    Dependency to get current authenticated user from session cookie.
    """
    if getattr(settings, "auth_provider", "local") == "none":
        return User(id="anonymous", username="Anonymous", role="user")

    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        session_id = auth.split(" ", 1)[1].strip()
    else:
        session_id = request.cookies.get(settings.session_cookie)
    if not session_id:
        return None
        
    # Find session in MongoDB
    # We store user sessions in a 'user_sessions' collection or verify against Redis
    # For simplicity, we'll implement a basic session lookup in MongoDB 'user_sessions'
    # schema: { "_id": session_id, "user_id": ..., "username": ..., "expires_at": ... }
    
    # Check if session exists and is valid
    # This is a simplified implementation. 
    # In a real app, you might use Redis for session storage.
    session_doc = await db.get_collection("user_sessions").find_one({"_id": session_id})
    
    if not session_doc:
        return None
        
    # Optionally check expiration
    import time
    if session_doc.get("expires_at", 0) < time.time():
        # Clean up expired session
        await db.get_collection("user_sessions").delete_one({"_id": session_id})
        return None
        
    return User(
        id=str(session_doc["user_id"]),
        username=session_doc["username"],
        role=session_doc.get("role", "user")
    )

async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Dependency to enforce authentication.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
