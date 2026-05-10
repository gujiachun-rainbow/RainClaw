"""
Tool REST API — 工具目录、规格查看与在线调试。

"""
from __future__ import annotations

import inspect
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from backend.user.dependencies import require_user, User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tooluniverse", tags=["tooluniverse"])

# ── ToolUniverse 单例 ──────────────────────────────────────────────

# ── 辅助 ──────────────────────────────────────────────────────────

_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def _sanitize(text: str) -> str:
    return _CTRL_RE.sub('', text) if text else ""


def _build_tools_list() -> List[Dict]:
    tools = []
    required_params: List[str] = []
    required_params.append("code")
    tools.append({
        "name": "get_datasource_by_code",
        "description": _sanitize("获取数据源，帮助agent进行数据分析"),
        "category": "数据源",
        "param_count": 1,
        "required_params": required_params,
        "has_examples": False,
        "has_return_schema": False,
    })
    return tools


# ── API 端点 ──────────────────────────────────────────────────────

class ToolRunRequest(BaseModel):
    arguments: Dict[str, Any]


@router.get("/tools")
async def list_tools(
    search: str = Query(default="", description="搜索关键词"),
    category: str = Query(default="", description="按类别过滤"),
    lang: str = Query(default="en", description="语言: en / zh"),
    _user: User = Depends(require_user),
):
    """列出所有 ToolUniverse 工具。"""
    tools = _build_tools_list()
    return {"tools": tools, "total": len(tools), "categories": ["数据源"]}


@router.get("/tools/{tool_name}")
async def get_tool_spec(
    tool_name: str,
    lang: str = Query(default="en", description="语言: en / zh"),
    _user: User = Depends(require_user),
):
    """获取单个工具的详细规格。"""
    # cache_key = f"tu_spec_v2_{tool_name}"
    # cached = _get_cached(cache_key)
    # if not cached:
    #     tu = _get_tu()
    #     if tu is None:
    #         raise HTTPException(status_code=503, detail="ToolUniverse is loading")

    #     try:
            # spec = tu.tool_specification(tool_name, format="openai")
    #     except Exception as exc:
    #         raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}") from exc

    #     if not spec:
    #         raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")

    #     raw_tool = None
    #     for t in (tu.all_tools if isinstance(tu.all_tools, list) else tu.all_tools.values()):
    #         if isinstance(t, dict) and t.get("name") == tool_name:
    #             raw_tool = t
    #             break

    #     cached = {
    #         **spec,
    #         "test_examples": [],
    #         "return_schema": None,
    #         "category": "",
    #         "source_file": "",
    #     }
    #     if raw_tool:
    #         cached["test_examples"] = raw_tool.get("test_examples", [])
    #         cached["return_schema"] = raw_tool.get("return_schema")
    #         cached["category"] = raw_tool.get("category", "") or raw_tool.get("type", "")
    #         cached["source_file"] = raw_tool.get("source_file", "")
    #         cached["description"] = _sanitize(cached.get("description", ""))

    #     _set_cached(cache_key, cached)

    # trans = _get_translation(lang)
    # if trans:
    #     return _translate_tool_spec(cached, trans)
    return {
        "name": "get_datasource_by_code",
        "description": "获取数据源信息，根据场景编码code获取数据源信息。",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "场景编码code",
                    "enum": None
                }
            },
            "required": ["code"]
        },
        "test_examples": [],
        "return_schema": None,
        "category": "数据源",
        "source_file": ""
    }


@router.post("/tools/{tool_name}/run")
async def run_tool(
    tool_name: str,
    body: ToolRunRequest,
    _user: User = Depends(require_user),
):
    from backend.deepagent.builtin_tools import get_datasource_by_code

    try:
        result = await get_datasource_by_code(body.arguments["code"])
    except Exception as exc:
        logger.error(f"[TU-API] Tool execution failed: {tool_name} - {exc}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {exc}") from exc

    # tu = _get_tu()
    # if tu is None:
    #     raise HTTPException(status_code=503, detail="ToolUniverse is loading")

    # try:
    #     result = tu.run({"name": tool_name, "arguments": body.arguments})
    #     if inspect.isawaitable(result):
    #         result = await result
    # except Exception as exc:
    #     logger.error(f"[TU-API] Tool execution failed: {tool_name} - {exc}")
    #     raise HTTPException(status_code=500, detail=f"Tool execution failed: {exc}") from exc

    return {"success": True, "result": result}


@router.get("/categories")
async def list_categories(
    lang: str = Query(default="en", description="语言: en / zh"),
    _user: User = Depends(require_user),
):
    # cache_key = "tu_tools_list"
    # cached = _get_cached(cache_key)
    # if cached is None:
    #     tu = _get_tu()
    #     if tu is None:
    #         raise HTTPException(status_code=503, detail="ToolUniverse is loading")
    #     cached = _build_tools_list(tu)
    #     _set_cached(cache_key, cached)

    # trans = _get_translation(lang)
    # cats_tr = trans.get("categories", {}) if trans else {}

    # counts: Dict[str, int] = {}
    # for t in cached:
    #     cat = t.get("category", "other") or "other"
    #     counts[cat] = counts.get(cat, 0) + 1

    return {
        "categories": [
            {"name": "get_datasource_by_code", "name_zh": "数据源获取", "count": 1}
        ]
    }
