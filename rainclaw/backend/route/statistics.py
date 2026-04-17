"""
Statistics 路由 - Token 使用统计 API。

路由：
  GET /statistics/summary   → 获取汇总统计数据
  GET /statistics/models    → 获取模型使用排行
  GET /statistics/trends    → 获取趋势数据
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from loguru import logger
from pydantic import BaseModel, Field

from backend.mongodb.db import db
from backend.user.dependencies import require_user, User

router = APIRouter(prefix="/statistics", tags=["Statistics"])

_db = db

# 汇率常量 (1 USD = ? CNY)
USD_TO_CNY = 7.3  # 美元兑人民币汇率


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class TokenDistribution(BaseModel):
    """Token 分布数据"""
    label: str
    value: int
    percentage: float


class SummaryResponse(BaseModel):
    """汇总统计响应"""
    total_cost_usd: float = Field(default=0.0, description="总消费（美元）")
    total_cost_cny: float = Field(default=0.0, description="总消费（人民币）")
    total_sessions: int = Field(default=0, description="总会话数")
    total_input_tokens: int = Field(default=0, description="总输入Token")
    total_output_tokens: int = Field(default=0, description="总输出Token")
    total_tokens: int = Field(default=0, description="总Token数")
    avg_per_session: float = Field(default=0.0, description="平均每会话Token")
    cost_trend: float = Field(default=0.0, description="消费趋势百分比")
    session_trend: float = Field(default=0.0, description="会话趋势百分比")
    token_trend: float = Field(default=0.0, description="Token趋势百分比")
    distribution: List[TokenDistribution] = Field(default_factory=list, description="Token分布")


class ModelUsage(BaseModel):
    """模型使用数据"""
    name: str = Field(description="模型名称")
    session_count: int = Field(default=0, description="会话数")
    input_tokens: int = Field(default=0, description="输入Token")
    output_tokens: int = Field(default=0, description="输出Token")
    total_tokens: int = Field(default=0, description="总Token")
    cost_usd: float = Field(default=0.0, description="消费（美元）")
    cost_cny: float = Field(default=0.0, description="消费（人民币）")


class ModelsResponse(BaseModel):
    """模型使用排行响应"""
    models: List[ModelUsage] = Field(default_factory=list, description="模型列表")


class TrendPoint(BaseModel):
    """趋势数据点"""
    date: str = Field(description="日期")
    sessions: int = Field(default=0)
    tokens: int = Field(default=0)
    cost_usd: float = Field(default=0.0, description="消费（美元）")
    cost_cny: float = Field(default=0.0, description="消费（人民币）")


class TrendsResponse(BaseModel):
    """趋势数据响应"""
    daily: List[TrendPoint] = Field(default_factory=list, description="每日数据")


class SessionUsage(BaseModel):
    """会话使用数据"""
    session_id: str = Field(description="会话ID")
    title: str = Field(default="", description="会话标题")
    model: str = Field(default="", description="模型名称")
    input_tokens: int = Field(default=0, description="输入Token")
    output_tokens: int = Field(default=0, description="输出Token")
    total_tokens: int = Field(default=0, description="总Token")
    cost_usd: float = Field(default=0.0, description="消费（美元）")
    cost_cny: float = Field(default=0.0, description="消费（人民币）")
    created_at: str = Field(default="", description="创建时间")
    status: str = Field(default="", description="会话状态")


class SessionsResponse(BaseModel):
    """会话使用列表响应"""
    sessions: List[SessionUsage] = Field(default_factory=list, description="会话列表")
    total: int = Field(default=0, description="总数")


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _get_time_range(time_range: str) -> tuple[datetime, datetime]:
    """根据时间范围参数获取起止时间"""
    now = datetime.now(timezone.utc)
    if time_range == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif time_range == "7days":
        start = now - timedelta(days=7)
    elif time_range == "30days":
        start = now - timedelta(days=30)
    else:  # all
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return start, now


def _get_previous_range(time_range: str) -> tuple[datetime, datetime]:
    """获取上一个周期的时间范围（用于计算趋势）"""
    now = datetime.now(timezone.utc)
    if time_range == "today":
        # 昨天
        end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=1)
    elif time_range == "7days":
        # 上周
        end = now - timedelta(days=7)
        start = end - timedelta(days=7)
    elif time_range == "30days":
        # 上月
        end = now - timedelta(days=30)
        start = end - timedelta(days=30)
    else:
        start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        end = datetime(2020, 1, 1, tzinfo=timezone.utc)
    return start, end


def _calculate_trend(current: float, previous: float) -> float:
    """计算趋势百分比"""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def _estimate_cost(input_tokens: int, output_tokens: int, model_name: str = "") -> float:
    """估算成本（基于常见模型定价，单位：美元/1K tokens）"""
    model_lower = (model_name or "").lower()

    # ═══════════════════════════════════════════════════════════════════════
    # Anthropic Claude 模型
    # ═══════════════════════════════════════════════════════════════════════
    if "claude-opus-4" in model_lower or "claude-4-opus" in model_lower:
        # Claude 4 Opus: $15/1M input, $75/1M output
        input_rate, output_rate = 0.015, 0.075
    elif "claude-sonnet-4" in model_lower or "claude-4-sonnet" in model_lower:
        # Claude 4 Sonnet: $3/1M input, $15/1M output
        input_rate, output_rate = 0.003, 0.015
    elif "claude-3-opus" in model_lower or "claude-opus" in model_lower:
        input_rate, output_rate = 0.015, 0.075
    elif "claude-3.5-sonnet" in model_lower or "claude-sonnet" in model_lower:
        input_rate, output_rate = 0.003, 0.015
    elif "claude-3-haiku" in model_lower or "claude-haiku" in model_lower:
        input_rate, output_rate = 0.00025, 0.00125

    # ═══════════════════════════════════════════════════════════════════════
    # OpenAI GPT 模型
    # ═══════════════════════════════════════════════════════════════════════
    elif "gpt-4.5" in model_lower:
        # GPT-4.5: $75/1M input, $150/1M output
        input_rate, output_rate = 0.075, 0.15
    elif "gpt-4o-mini" in model_lower:
        # GPT-4o Mini: $0.15/1M input, $0.6/1M output
        input_rate, output_rate = 0.00015, 0.0006
    elif "gpt-4o" in model_lower:
        # GPT-4o: $2.5/1M input, $10/1M output
        input_rate, output_rate = 0.0025, 0.01
    elif "gpt-4-turbo" in model_lower or "gpt-4-0" in model_lower:
        # GPT-4 Turbo: $10/1M input, $30/1M output
        input_rate, output_rate = 0.01, 0.03
    elif "gpt-4-32k" in model_lower:
        input_rate, output_rate = 0.06, 0.12
    elif "gpt-4" in model_lower:
        input_rate, output_rate = 0.03, 0.06
    elif "o3-mini" in model_lower:
        # o3-mini: $1.1/1M input, $4.4/1M output
        input_rate, output_rate = 0.0011, 0.0044
    elif "o1" in model_lower:
        # o1: $15/1M input, $60/1M output
        input_rate, output_rate = 0.015, 0.06
    elif "gpt-3.5-turbo" in model_lower or "gpt-3.5" in model_lower:
        input_rate, output_rate = 0.0005, 0.0015

    # ═══════════════════════════════════════════════════════════════════════
    # DeepSeek 模型
    # ═══════════════════════════════════════════════════════════════════════
    elif "deepseek-reasoner" in model_lower or "deepseek-r1" in model_lower:
        # DeepSeek R1: ¥4/1M input (cache miss), ¥16/1M output ≈ $0.55/$2.2
        input_rate, output_rate = 0.00055, 0.0022
    elif "deepseek-chat" in model_lower or "deepseek-v3" in model_lower:
        # DeepSeek V3: ¥0.5/1M input (cache miss), ¥2/1M output ≈ $0.07/$0.28
        input_rate, output_rate = 0.00007, 0.00028
    elif "deepseek" in model_lower:
        # Default DeepSeek pricing
        input_rate, output_rate = 0.00007, 0.00028

    # ═══════════════════════════════════════════════════════════════════════
    # 阿里云通义千问 (Qwen/通义)
    # ═══════════════════════════════════════════════════════════════════════
    elif "qwen-max" in model_lower or "qwen2.5-max" in model_lower:
        # Qwen Max: ¥20/1M input, ¥60/1M output ≈ $2.75/$8.25
        input_rate, output_rate = 0.00275, 0.00825
    elif "qwen-plus" in model_lower or "qwen2.5-plus" in model_lower:
        # Qwen Plus: ¥4/1M input, ¥12/1M output ≈ $0.55/$1.65
        input_rate, output_rate = 0.00055, 0.00165
    elif "qwen-turbo" in model_lower or "qwen2.5-turbo" in model_lower:
        # Qwen Turbo: ¥0.3/1M input, ¥0.6/1M output ≈ $0.04/$0.08
        input_rate, output_rate = 0.00004, 0.00008
    elif "qwen-long" in model_lower:
        # Qwen Long: ¥0.5/1M input
        input_rate, output_rate = 0.00007, 0.00007
    elif "qwen" in model_lower or "tongyi" in model_lower or "通义" in model_name:
        # Default Qwen pricing
        input_rate, output_rate = 0.00055, 0.00165

    # ═══════════════════════════════════════════════════════════════════════
    # 智谱 GLM 模型
    # ═══════════════════════════════════════════════════════════════════════
    elif "glm-4-plus" in model_lower:
        # GLM-4 Plus: ¥50/1M input, ¥50/1M output ≈ $6.85/$6.85
        input_rate, output_rate = 0.00685, 0.00685
    elif "glm-4-air" in model_lower:
        # GLM-4 Air: ¥1/1M input, ¥1/1M output ≈ $0.14/$0.14
        input_rate, output_rate = 0.00014, 0.00014
    elif "glm-4-flash" in model_lower:
        # GLM-4 Flash: Free
        input_rate, output_rate = 0.0, 0.0
    elif "glm-4" in model_lower:
        # GLM-4: ¥100/1M input, ¥100/1M output ≈ $13.7/$13.7
        input_rate, output_rate = 0.0137, 0.0137
    elif "glm" in model_lower:
        # Default GLM pricing
        input_rate, output_rate = 0.00685, 0.00685

    # ═══════════════════════════════════════════════════════════════════════
    # 月之暗面 Kimi (Moonshot)
    # ═══════════════════════════════════════════════════════════════════════
    elif "moonshot-v1-128k" in model_lower or "kimi-128k" in model_lower:
        # Moonshot V1 128K: ¥14/1M input, ¥14/1M output ≈ $1.92/$1.92
        input_rate, output_rate = 0.00192, 0.00192
    elif "moonshot-v1-32k" in model_lower or "kimi-32k" in model_lower:
        # Moonshot V1 32K: ¥14/1M input, ¥14/1M output
        input_rate, output_rate = 0.00192, 0.00192
    elif "moonshot-v1-8k" in model_lower or "kimi-8k" in model_lower or "moonshot" in model_lower or "kimi" in model_lower:
        # Moonshot V1 8K: ¥12/1M input, ¥12/1M output ≈ $1.65/$1.65
        input_rate, output_rate = 0.00165, 0.00165

    # ═══════════════════════════════════════════════════════════════════════
    # 百度文心一言 (ERNIE)
    # ═══════════════════════════════════════════════════════════════════════
    elif "ernie-4.0-8k" in model_lower or "ernie-4" in model_lower:
        # ERNIE 4.0: ¥120/1M input, ¥120/1M output ≈ $16.44/$16.44
        input_rate, output_rate = 0.01644, 0.01644
    elif "ernie-3.5-8k" in model_lower or "ernie-3.5" in model_lower:
        # ERNIE 3.5: ¥12/1M input, ¥12/1M output ≈ $1.64/$1.64
        input_rate, output_rate = 0.00164, 0.00164
    elif "ernie-speed" in model_lower or "ernie-lite" in model_lower:
        # ERNIE Speed/Lite: Free
        input_rate, output_rate = 0.0, 0.0
    elif "ernie" in model_lower:
        input_rate, output_rate = 0.00164, 0.00164

    # ═══════════════════════════════════════════════════════════════════════
    # 字节豆包 (Doubao)
    # ═══════════════════════════════════════════════════════════════════════
    elif "doubao-pro-256k" in model_lower:
        # Doubao Pro 256K: ¥5/1M input, ¥5/1M output ≈ $0.68/$0.68
        input_rate, output_rate = 0.00068, 0.00068
    elif "doubao-pro-128k" in model_lower:
        # Doubao Pro 128K: ¥5/1M input, ¥5/1M output
        input_rate, output_rate = 0.00068, 0.00068
    elif "doubao-pro-32k" in model_lower or "doubao-pro" in model_lower:
        # Doubao Pro 32K: ¥0.8/1M input, ¥2/1M output ≈ $0.11/$0.27
        input_rate, output_rate = 0.00011, 0.00027
    elif "doubao-lite" in model_lower:
        # Doubao Lite: ¥0.3/1M input, ¥0.6/1M output ≈ $0.04/$0.08
        input_rate, output_rate = 0.00004, 0.00008
    elif "doubao" in model_lower:
        input_rate, output_rate = 0.00011, 0.00027

    # ═══════════════════════════════════════════════════════════════════════
    # MiniMax
    # ═══════════════════════════════════════════════════════════════════════
    elif "abab6.5-chat" in model_lower or "abab6.5" in model_lower:
        # ABAB 6.5: ¥30/1M input, ¥60/1M output ≈ $4.11/$8.22
        input_rate, output_rate = 0.00411, 0.00822
    elif "abab5.5-chat" in model_lower or "abab5.5" in model_lower:
        # ABAB 5.5: ¥15/1M input, ¥30/1M output ≈ $2.05/$4.11
        input_rate, output_rate = 0.00205, 0.00411
    elif "abab" in model_lower:
        input_rate, output_rate = 0.00205, 0.00411

    # ═══════════════════════════════════════════════════════════════════════
    # 讯飞星火 (Spark)
    # ═══════════════════════════════════════════════════════════════════════
    elif "spark-v4.0" in model_lower or "spark4.0" in model_lower:
        # Spark V4.0: ¥70/1M input, ¥70/1M output ≈ $9.59/$9.59
        input_rate, output_rate = 0.00959, 0.00959
    elif "spark-v3.5" in model_lower or "spark3.5" in model_lower:
        # Spark V3.5: ¥18/1M input, ¥18/1M output ≈ $2.47/$2.47
        input_rate, output_rate = 0.00247, 0.00247
    elif "spark-v3.0" in model_lower or "spark3.0" in model_lower:
        # Spark V3.0: ¥36/1M input, ¥36/1M output ≈ $4.93/$4.93
        input_rate, output_rate = 0.00493, 0.00493
    elif "spark" in model_lower or "星火" in model_name:
        input_rate, output_rate = 0.00247, 0.00247

    # ═══════════════════════════════════════════════════════════════════════
    # Google Gemini
    # ═══════════════════════════════════════════════════════════════════════
    elif "gemini-2.0-flash" in model_lower:
        # Gemini 2.0 Flash: Free tier available, paid $0.1/1M input, $0.4/1M output
        input_rate, output_rate = 0.0001, 0.0004
    elif "gemini-1.5-pro" in model_lower:
        # Gemini 1.5 Pro: $1.25/1M input, $5/1M output
        input_rate, output_rate = 0.00125, 0.005
    elif "gemini-1.5-flash" in model_lower:
        # Gemini 1.5 Flash: $0.075/1M input, $0.3/1M output
        input_rate, output_rate = 0.000075, 0.0003
    elif "gemini" in model_lower:
        input_rate, output_rate = 0.0001, 0.0004

    # ═══════════════════════════════════════════════════════════════════════
    # Meta Llama
    # ═══════════════════════════════════════════════════════════════════════
    elif "llama-3.3-70b" in model_lower or "llama3.3-70b" in model_lower:
        # Llama 3.3 70B: ~$0.6/1M input, $0.6/1M output
        input_rate, output_rate = 0.0006, 0.0006
    elif "llama-3.1-405b" in model_lower or "llama3.1-405b" in model_lower:
        # Llama 3.1 405B: ~$2.7/1M input, $2.7/1M output
        input_rate, output_rate = 0.0027, 0.0027
    elif "llama-3.1-70b" in model_lower or "llama3.1-70b" in model_lower:
        input_rate, output_rate = 0.0006, 0.0006
    elif "llama" in model_lower:
        input_rate, output_rate = 0.0006, 0.0006

    # ═══════════════════════════════════════════════════════════════════════
    # Mistral
    # ═══════════════════════════════════════════════════════════════════════
    elif "mistral-large" in model_lower:
        # Mistral Large: $2/1M input, $6/1M output
        input_rate, output_rate = 0.002, 0.006
    elif "mistral-medium" in model_lower:
        input_rate, output_rate = 0.001, 0.003
    elif "mistral-small" in model_lower:
        input_rate, output_rate = 0.0002, 0.0006
    elif "mistral" in model_lower or "codestral" in model_lower:
        input_rate, output_rate = 0.0002, 0.0006

    # ═══════════════════════════════════════════════════════════════════════
    # 默认价格
    # ═══════════════════════════════════════════════════════════════════════
    else:
        # 默认价格：$1/1M input, $2/1M output
        input_rate, output_rate = 0.001, 0.002

    return (input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)


async def _aggregate_statistics(
    user_id: str,
    start_time: datetime,
    end_time: datetime
) -> Dict[str, Any]:
    """聚合指定时间范围内的统计数据"""
    # 数据库中的 updated_at 是秒级时间戳，不是毫秒
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())

    logger.info(f"[Statistics] Aggregating for user={user_id}, start={start_ts}, end={end_ts}")

    # 查询用户的所有会话（不限状态，因为可能还在运行或已完成）
    query = {
        "user_id": user_id,
        "updated_at": {"$gte": start_ts, "$lte": end_ts}
    }

    sessions = await _db.get_collection("sessions").find(query).to_list(length=None)
    logger.info(f"[Statistics] Found {len(sessions)} sessions for user")

    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0
    session_count = len(sessions)
    model_stats = defaultdict(lambda: {
        "session_count": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0.0
    })
    daily_stats = defaultdict(lambda: {"sessions": 0, "tokens": 0, "cost_usd": 0.0})

    for session in sessions:
        # 从 events 中提取统计数据
        events = session.get("events", [])
        session_input = 0
        session_output = 0
        model_name = ""

        # 获取模型配置 - 支持多种字段名
        model_config = session.get("model_config", {})
        if isinstance(model_config, dict):
            # 优先级: model_name > model > model_id
            model_name = (
                model_config.get("model_name", "") or
                model_config.get("model", "") or
                model_config.get("model_id", "")
            )

        # 如果 model_config 为空，尝试从其他字段获取
        if not model_name:
            model_name = session.get("model", "") or session.get("model_id", "")

        # 如果仍然为空，使用默认名称
        if not model_name:
            model_name = "Unknown Model"

        for event in events:
            if event.get("event") == "done":
                data = event.get("data", {})
                stats = data.get("statistics", {})

                # 累加 token（支持新旧格式）
                input_tokens = stats.get("input_tokens", 0) or 0
                output_tokens = stats.get("output_tokens", 0) or 0
                # 兼容旧格式：如果没有 input/output 分离，使用 token_count
                if not input_tokens and not output_tokens:
                    token_count = stats.get("token_count", 0) or 0
                    # 假设 70% 输入，30% 输出
                    input_tokens = int(token_count * 0.7)
                    output_tokens = token_count - input_tokens

                session_input += input_tokens
                session_output += output_tokens

        # 计算成本（美元）
        session_cost_usd = _estimate_cost(session_input, session_output, model_name)
        total_input_tokens += session_input
        total_output_tokens += session_output
        total_cost_usd += session_cost_usd

        # 按模型聚合（model_name 始终有值，默认为 "Unknown Model"）
        model_stats[model_name]["session_count"] += 1
        model_stats[model_name]["input_tokens"] += session_input
        model_stats[model_name]["output_tokens"] += session_output
        model_stats[model_name]["cost_usd"] += session_cost_usd

        # 按日期聚合
        updated_at = session.get("updated_at", 0)
        if updated_at:
            # updated_at 已经是秒级时间戳
            date_str = datetime.fromtimestamp(updated_at, tz=timezone.utc).strftime("%Y-%m-%d")
            daily_stats[date_str]["sessions"] += 1
            daily_stats[date_str]["tokens"] += session_input + session_output
            daily_stats[date_str]["cost_usd"] += session_cost_usd

    logger.info(f"[Statistics] Result: input={total_input_tokens}, output={total_output_tokens}, sessions={session_count}")

    return {
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_input_tokens + total_output_tokens,
        "total_cost_usd": total_cost_usd,
        "session_count": session_count,
        "model_stats": dict(model_stats),
        "daily_stats": dict(daily_stats)
    }


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/summary", response_model=SummaryResponse)
async def get_statistics_summary(
    time_range: str = Query("7days", description="时间范围: today, 7days, 30days, all"),
    current_user: User = Depends(require_user)
) -> SummaryResponse:
    """获取统计数据汇总"""
    try:
        start_time, end_time = _get_time_range(time_range)
        prev_start, prev_end = _get_previous_range(time_range)

        # 获取当前周期数据
        current_stats = await _aggregate_statistics(current_user.id, start_time, end_time)

        # 获取上一周期数据（用于计算趋势）
        prev_stats = await _aggregate_statistics(current_user.id, prev_start, prev_end)

        total_tokens = current_stats["total_tokens"]
        session_count = current_stats["session_count"]

        # 计算 Token 分布
        distribution = []
        if total_tokens > 0:
            input_pct = (current_stats["total_input_tokens"] / total_tokens) * 100
            output_pct = (current_stats["total_output_tokens"] / total_tokens) * 100

            distribution = [
                TokenDistribution(
                    label="Input Tokens",
                    value=current_stats["total_input_tokens"],
                    percentage=round(input_pct, 1)
                ),
                TokenDistribution(
                    label="Output Tokens",
                    value=current_stats["total_output_tokens"],
                    percentage=round(output_pct, 1)
                ),
            ]

        return SummaryResponse(
            total_cost_usd=round(current_stats["total_cost_usd"], 4),
            total_cost_cny=round(current_stats["total_cost_usd"] * USD_TO_CNY, 4),
            total_sessions=session_count,
            total_input_tokens=current_stats["total_input_tokens"],
            total_output_tokens=current_stats["total_output_tokens"],
            total_tokens=total_tokens,
            avg_per_session=round(total_tokens / session_count, 0) if session_count > 0 else 0,
            cost_trend=_calculate_trend(current_stats["total_cost_usd"], prev_stats["total_cost_usd"]),
            session_trend=_calculate_trend(session_count, prev_stats["session_count"]),
            token_trend=_calculate_trend(total_tokens, prev_stats["total_tokens"]),
            distribution=distribution
        )

    except Exception as e:
        logger.exception(f"Failed to get statistics summary: {e}")
        return SummaryResponse()


@router.get("/models", response_model=ModelsResponse)
async def get_statistics_models(
    time_range: str = Query("7days", description="时间范围: today, 7days, 30days, all"),
    current_user: User = Depends(require_user)
) -> ModelsResponse:
    """获取模型使用排行"""
    try:
        start_time, end_time = _get_time_range(time_range)
        stats = await _aggregate_statistics(current_user.id, start_time, end_time)

        models = []
        for model_name, model_data in stats["model_stats"].items():
            cost_usd = model_data["cost_usd"]
            models.append(ModelUsage(
                name=model_name,
                session_count=model_data["session_count"],
                input_tokens=model_data["input_tokens"],
                output_tokens=model_data["output_tokens"],
                total_tokens=model_data["input_tokens"] + model_data["output_tokens"],
                cost_usd=round(cost_usd, 4),
                cost_cny=round(cost_usd * USD_TO_CNY, 4)
            ))

        # 按总 Token 排序
        models.sort(key=lambda x: x.total_tokens, reverse=True)

        return ModelsResponse(models=models[:10])  # 返回前10个

    except Exception as e:
        logger.exception(f"Failed to get model statistics: {e}")
        return ModelsResponse()


@router.get("/trends", response_model=TrendsResponse)
async def get_statistics_trends(
    time_range: str = Query("7days", description="时间范围: today, 7days, 30days, all"),
    current_user: User = Depends(require_user)
) -> TrendsResponse:
    """获取趋势数据"""
    try:
        start_time, end_time = _get_time_range(time_range)
        stats = await _aggregate_statistics(current_user.id, start_time, end_time)

        daily = []
        for date_str, day_data in sorted(stats["daily_stats"].items()):
            cost_usd = day_data["cost_usd"]
            daily.append(TrendPoint(
                date=date_str,
                sessions=day_data["sessions"],
                tokens=day_data["tokens"],
                cost_usd=round(cost_usd, 4),
                cost_cny=round(cost_usd * USD_TO_CNY, 4)
            ))

        return TrendsResponse(daily=daily)

    except Exception as e:
        logger.exception(f"Failed to get trend statistics: {e}")
        return TrendsResponse()


@router.get("/sessions", response_model=SessionsResponse)
async def get_statistics_sessions(
    time_range: str = Query("7days", description="时间范围: today, 7days, 30days, all"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_user)
) -> SessionsResponse:
    """获取会话使用明细"""
    try:
        start_time, end_time = _get_time_range(time_range)
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        # 查询会话
        query = {
            "user_id": current_user.id,
            "updated_at": {"$gte": start_ts, "$lte": end_ts}
        }

        # 获取总数
        total = await _db.get_collection("sessions").count_documents(query)

        # 分页查询
        skip = (page - 1) * page_size
        sessions = await _db.get_collection("sessions").find(query).sort("updated_at", -1).skip(skip).limit(page_size).to_list(length=page_size)

        session_list = []
        for session in sessions:
            # 从 events 中提取 token 统计
            events = session.get("events", [])
            session_input = 0
            session_output = 0
            model_name = ""

            # 获取模型配置 - 支持多种字段名
            model_config = session.get("model_config", {})
            if isinstance(model_config, dict):
                # 优先级: model_name > model > model_id
                model_name = (
                    model_config.get("model_name", "") or
                    model_config.get("model", "") or
                    model_config.get("model_id", "")
                )

            # 如果 model_config 为空，尝试从其他字段获取
            if not model_name:
                model_name = session.get("model", "") or session.get("model_id", "")

            # 如果仍然为空，使用默认名称
            if not model_name:
                model_name = "Unknown Model"

            for event in events:
                if event.get("event") == "done":
                    data = event.get("data", {})
                    stats = data.get("statistics", {})

                    input_tokens = stats.get("input_tokens", 0) or 0
                    output_tokens = stats.get("output_tokens", 0) or 0

                    if not input_tokens and not output_tokens:
                        token_count = stats.get("token_count", 0) or 0
                        input_tokens = int(token_count * 0.7)
                        output_tokens = token_count - input_tokens

                    session_input += input_tokens
                    session_output += output_tokens

            # 获取会话标题
            title = session.get("title", "")
            if not title:
                # 从第一条用户消息提取标题
                messages = session.get("messages", [])
                for msg in messages:
                    if msg.get("role") == "user":
                        content = msg.get("content", "")
                        title = content[:50] + "..." if len(content) > 50 else content
                        break

            # 格式化创建时间
            created_at_ts = session.get("created_at", 0)
            if created_at_ts:
                created_at = datetime.fromtimestamp(created_at_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            else:
                created_at = ""

            session_cost_usd = _estimate_cost(session_input, session_output, model_name)

            session_list.append(SessionUsage(
                session_id=str(session.get("_id", "")),
                title=title,
                model=model_name,
                input_tokens=session_input,
                output_tokens=session_output,
                total_tokens=session_input + session_output,
                cost_usd=round(session_cost_usd, 4),
                cost_cny=round(session_cost_usd * USD_TO_CNY, 4),
                created_at=created_at,
                status=session.get("status", "completed")
            ))

        return SessionsResponse(sessions=session_list, total=total)

    except Exception as e:
        logger.exception(f"Failed to get session statistics: {e}")
        return SessionsResponse()
