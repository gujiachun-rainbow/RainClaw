from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from langchain_core.messages import SystemMessage, HumanMessage
from backend.deepagent.engine import get_llm_model
from backend.models import get_model_config, list_user_models
from backend.user.dependencies import require_user, User


router = APIRouter(prefix="/science", tags=["science"])


class ApiResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="ok")
    data: Any = Field(default=None)


class OptimizePromptRequest(BaseModel):
    query: str
    model_config_id: Optional[str] = None


class OptimizePromptResponse(BaseModel):
    optimized_query: str


_SYSTEM_PROMPT = (
    "You are a helpful assistant that optimizes user queries for a scientific "
    "research agent. The user will provide a query. You should rewrite it to be "
    "more precise, detailed, and structured, suitable for a research agent. "
    "Keep the original intent. Output ONLY the rewritten query without any explanation."
)


async def _resolve_model_config(model_config_id: Optional[str], user_id: str) -> Optional[dict]:
    """Resolve model config dict: explicit id > user's first active model > None (global default)."""
    if model_config_id:
        mc = await get_model_config(model_config_id)
        if mc:
            return mc.model_dump()
    models = await list_user_models(user_id)
    if models:
        return models[0].model_dump()
    return None


@router.post("/optimize_prompt", response_model=ApiResponse)
async def optimize_prompt(
    body: OptimizePromptRequest,
    current_user: User = Depends(require_user),
) -> ApiResponse:
    try:
        config_dict = await _resolve_model_config(body.model_config_id, current_user.id)
        llm = get_llm_model(config=config_dict, streaming=False)
        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=body.query),
        ]
        result = await llm.ainvoke(messages)
        return ApiResponse(
            data=OptimizePromptResponse(optimized_query=result.content).model_dump()
        )
    except Exception as exc:
        logger.exception("optimize_prompt failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
