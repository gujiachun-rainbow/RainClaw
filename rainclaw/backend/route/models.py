from typing import List, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
import time
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from backend.user.dependencies import get_current_user, require_user, User
from backend.mongodb.db import db
from backend.models import ModelConfig, CreateModelRequest, UpdateModelRequest, list_user_models

router = APIRouter(prefix="/models", tags=["models"])
from loguru import logger

class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)

async def verify_model_connection(provider: str, base_url: str | None, api_key: str | None, model_name: str):
    """
    Verify model availability by making a simple request.
    """
    logger.info(f"[verify_model] provider={provider}, model_name={model_name}, base_url={base_url}, has_api_key={bool(api_key)}")
    try:
        if not api_key:
            raise ValueError("API Key is required for verification")

        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            logger.info("[verify_model] Using ChatGoogleGenerativeAI for Gemini")
            chat = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                max_output_tokens=5,
                timeout=10,
            )
        else:
            logger.info(f"[verify_model] Using ChatOpenAI, base_url={base_url or '(default)'}")
            chat = ChatOpenAI(
                model=model_name,
                api_key=api_key,
                base_url=base_url if base_url else None,
                max_tokens=5,
                timeout=10,
            )
        
        logger.info("[verify_model] Sending test message...")
        await chat.ainvoke([HumanMessage(content="Hi")])
        logger.info("[verify_model] Verification succeeded")
        return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[verify_model] Verification failed: {type(e).__name__}: {e}")
        detail = _extract_api_error(e)
        raise HTTPException(status_code=400, detail=detail)


def _extract_api_error(e: Exception) -> str:
    """Extract the original API error message from provider SDK exceptions."""
    import json as _json

    # openai SDK errors (NotFoundError, AuthenticationError, etc.) have a `body` dict
    body = getattr(e, 'body', None)
    if isinstance(body, dict):
        err_obj = body.get('error', body)
        if isinstance(err_obj, dict):
            msg = err_obj.get('message') or err_obj.get('msg')
            err_type = err_obj.get('type', '')
            if msg:
                return f"{msg} ({err_type})" if err_type else str(msg)

    # Some SDKs attach a `response` object with the raw HTTP body
    resp = getattr(e, 'response', None)
    if resp is not None:
        try:
            text = resp.text if hasattr(resp, 'text') else str(resp)
            data = _json.loads(text)
            err_obj = data.get('error', data)
            if isinstance(err_obj, dict):
                msg = err_obj.get('message') or err_obj.get('msg')
                if msg:
                    return str(msg)
        except Exception:
            pass

    return str(e)

@router.get("", response_model=ApiResponse)
async def list_models(current_user: User = Depends(require_user)):
    """List all available models (System + User Defined)"""
    models = await list_user_models(current_user.id)
    results = []
    for m in models:
        d = m.model_dump()
        if d.get("api_key"):
            d["api_key"] = "********"
        results.append(d)
    return ApiResponse(data=results)

@router.post("", response_model=ApiResponse)
async def create_model(body: CreateModelRequest, current_user: User = Depends(require_user)):
    """Add a user defined model"""
    logger.info(f"[create_model] provider={body.provider}, model_name={body.model_name}, "
                f"name={body.name}, base_url={body.base_url}, has_api_key={bool(body.api_key)}")
    await verify_model_connection(body.provider, body.base_url, body.api_key, body.model_name)

    model_id = str(uuid.uuid4())
    now = int(time.time())
    
    new_model = ModelConfig(
        id=model_id,
        name=body.name,
        provider=body.provider,
        base_url=body.base_url,
        api_key=body.api_key,
        model_name=body.model_name,
        context_window=body.context_window,
        is_system=False,
        user_id=current_user.id,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    
    doc = new_model.model_dump()
    doc["_id"] = doc.pop("id")
    
    await db.get_collection("models").insert_one(doc)
    
    # Return with id
    return ApiResponse(data=new_model.model_dump())

class DetectContextWindowRequest(BaseModel):
    provider: str
    base_url: str | None = None
    api_key: str | None = None
    model_name: str
    model_id: str | None = None


async def _probe_context_window_via_api(base_url: str | None, api_key: str | None, model_name: str) -> int | None:
    """Try to retrieve context window from the provider's /models/{model} endpoint."""
    if not api_key:
        return None
    import httpx
    url = (base_url or "https://api.openai.com/v1").rstrip("/")
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{url}/models/{model_name}", headers=headers)
            if resp.status_code != 200:
                return None
            data = resp.json()
            for key in ("context_window", "context_length", "max_model_len", "max_tokens"):
                val = data.get(key)
                if isinstance(val, int) and val >= 1024:
                    return val
    except Exception:
        pass
    return None


async def _probe_gemini_context_window(api_key: str | None, model_name: str) -> int | None:
    """Probe context window via Google Generative AI API."""
    if not api_key:
        return None
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}?key={api_key}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            data = resp.json()
            val = data.get("inputTokenLimit")
            if isinstance(val, int) and val >= 1024:
                return val
    except Exception:
        pass
    return None


@router.post("/detect-context-window", response_model=ApiResponse)
async def detect_context_window(body: DetectContextWindowRequest, current_user: User = Depends(require_user)):
    """Detect context window: try local table first, then probe via API."""
    from backend.deepagent.engine import _infer_context_window

    inferred = _infer_context_window(body.model_name)
    if inferred is not None:
        return ApiResponse(data={"context_window": inferred, "source": "local"})

    api_key = body.api_key
    base_url = body.base_url
    if body.model_id and (not api_key):
        existing = await db.get_collection("models").find_one({"_id": body.model_id})
        if existing:
            api_key = api_key or existing.get("api_key")
            base_url = base_url or existing.get("base_url")

    if body.provider == "gemini":
        probed = await _probe_gemini_context_window(api_key, body.model_name)
    else:
        probed = await _probe_context_window_via_api(base_url, api_key, body.model_name)
    if probed is not None:
        return ApiResponse(data={"context_window": probed, "source": "api"})

    raise HTTPException(status_code=404, detail=f"Unable to detect context window for model '{body.model_name}'. Please set it manually.")


@router.put("/{model_id}", response_model=ApiResponse)
async def update_model(model_id: str, body: UpdateModelRequest, current_user: User = Depends(require_user)):
    """Update a user defined model"""
    existing = await db.get_collection("models").find_one({"_id": model_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")
        
    if existing.get("is_system"):
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Cannot edit this model")
    else:
        if existing.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot edit this model")
        
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        return ApiResponse(data={"id": model_id})
    
    merged_base_url = update_data.get("base_url", existing.get("base_url"))
    merged_api_key = update_data.get("api_key", existing.get("api_key"))
    merged_model_name = update_data.get("model_name", existing.get("model_name"))
    merged_provider = existing.get("provider")
    
    if any(k in update_data for k in ["base_url", "api_key", "model_name"]):
        await verify_model_connection(merged_provider, merged_base_url, merged_api_key, merged_model_name)

    update_data["updated_at"] = int(time.time())
    
    await db.get_collection("models").update_one(
        {"_id": model_id},
        {"$set": update_data}
    )
    
    return ApiResponse(data={"id": model_id})


@router.delete("/{model_id}", response_model=ApiResponse)
async def delete_model(model_id: str, current_user: User = Depends(require_user)):
    """Delete a user defined model"""
    existing = await db.get_collection("models").find_one({"_id": model_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")
        
    if existing.get("is_system"):
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Cannot delete this model")
    else:
        if existing.get("user_id") != current_user.id:
            raise HTTPException(status_code=403, detail="Cannot delete this model")
        
    await db.get_collection("models").delete_one({"_id": model_id})
    return ApiResponse(data={"ok": True})
