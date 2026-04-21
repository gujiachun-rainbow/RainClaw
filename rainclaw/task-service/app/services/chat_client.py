"""Call Chat Service to run task prompt and get LLM output."""
from typing import Any, Optional

import httpx
from loguru import logger

from app.core.config import settings


async def run_task_chat(
    task_id: str,
    prompt: str,
    event_callback_url: Optional[str] = None,
) -> dict[str, Any]:
    """
    POST to Chat Service /api/v1/chat (task invocation).
    Returns {"chat_id": str, "output": str} on success, or {"error": str} on failure.
    """
    url = f"{settings.chat_service_url.rstrip('/')}/api/v1/chat"
    payload: dict[str, Any] = {
        "input": prompt,
        "source": "task",
        "task_id": task_id,
    }
    if event_callback_url:
        payload["event_callback_url"] = event_callback_url
    headers = {"Content-Type": "application/json"}
    if settings.chat_service_api_key:
        headers["X-API-Key"] = settings.chat_service_api_key
    try:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                return {"error": f"Chat service returned {resp.status_code}: {resp.text[:500]}"}
            data = resp.json()
            if "error" in data:
                return data
            return {
                "chat_id": data.get("chat_id", ""),
                "output": data.get("output", ""),
            }
    except httpx.TimeoutException:
        return {"error": "Chat service request timeout"}
    except Exception as e:
        logger.exception("run_task_chat failed")
        return {"error": str(e)}
