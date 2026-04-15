"""
Plan 类型定义（精简版，替代 planner_middleware.py）。

仅保留前端 SSE 事件所需的 PlanStep 和 normalize_plan_steps。
"""
import time
from typing_extensions import NotRequired, TypedDict


class PlanStep(TypedDict):
    id: str
    content: str
    status: str
    tools: list[str]
    files: list[str]
    priority: str
    inputs: NotRequired[dict]
    outputs: NotRequired[dict]
    created_at: int


def normalize_plan_steps(plan: list[PlanStep]) -> list[PlanStep]:
    """对计划步骤进行字段归一化，保证前端展示具备稳定结构。"""
    now = int(time.time())
    normalized: list[PlanStep] = []
    for index, step in enumerate(plan):
        normalized.append({
            "id": step.get("id") or f"step-{index + 1}",
            "content": step["content"],
            "status": step.get("status") or "pending",
            "priority": step.get("priority") or "medium",
            "tools": step.get("tools") or [],
            "files": step.get("files") or [],
            "created_at": step.get("created_at") or now,
            "inputs": step.get("inputs") or {},
            "outputs": step.get("outputs") or {},
        })
    return normalized
