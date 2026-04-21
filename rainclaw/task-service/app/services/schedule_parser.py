"""
自然语言定时描述转 crontab：优先调用主服务（使用系统配置的用户模型），
未配置模型时主服务返回明确提示，本模块将该提示原样抛给前端。
"""
import re
from typing import List, Optional

import httpx
from loguru import logger

from app.core.config import settings

# Crontab 格式校验
CRONTAB_RE = re.compile(r"^\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


class ScheduleParseError(Exception):
    """解析失败且需要将消息返回给用户（如未配置大模型）。可携带基于用户输入推断的建议。"""
    def __init__(self, message: str, suggestions: Optional[List[str]] = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


async def parse_schedule_to_crontab(schedule_desc: str, model_config_id: Optional[str] = None) -> Optional[str]:
    """
    调用主服务（Chat Service）的「定时描述转 crontab」接口，使用系统配置的大模型。
    若主服务返回 400 且提示未配置大模型，抛出 ScheduleParseError，由 API 层返回给用户。
    若主服务不可用或解析失败，尝试简单兜底规则后返回 None。
    """
    if not (schedule_desc and schedule_desc.strip()):
        return None
    desc = schedule_desc.strip()[:200]

    url = f"{settings.chat_service_url.rstrip('/')}/api/v1/task/parse-schedule"
    headers = {"Content-Type": "application/json"}
    if settings.chat_service_api_key:
        headers["X-API-Key"] = settings.chat_service_api_key

    payload: dict = {"schedule_desc": desc}
    if model_config_id:
        payload["model_config_id"] = model_config_id

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                crontab = (data.get("crontab") or "").strip()
                if CRONTAB_RE.match(crontab):
                    return crontab
                return _fallback_crontab(desc)
            if resp.status_code == 400:
                try:
                    err = resp.json()
                    detail = err.get("detail") or err.get("message") or "无法解析定时描述"
                    if isinstance(detail, dict):
                        msg = detail.get("message") or detail.get("detail") or "无法解析定时描述"
                        suggestions = detail.get("suggestions")
                        if isinstance(suggestions, list):
                            suggestions = [s for s in suggestions if isinstance(s, str) and s.strip()][:3]
                        else:
                            suggestions = []
                        raise ScheduleParseError(msg, suggestions=suggestions or None)
                    raise ScheduleParseError(detail if isinstance(detail, str) else "无法解析定时描述")
                except ScheduleParseError:
                    raise
                except Exception:
                    raise ScheduleParseError("无法解析定时描述")
            logger.warning(f"Parse schedule backend returned {resp.status_code} {resp.text[:200]}")
            return _fallback_crontab(desc)
    except ScheduleParseError:
        raise
    except Exception as e:
        logger.warning(f"Parse schedule request failed: {e}")
        return _fallback_crontab(desc)


def _fallback_crontab(desc: str) -> Optional[str]:
    """简单兜底规则（主服务不可用时的本地规则）。"""
    if "每" in desc and "分钟" in desc:
        m = re.search(r"(\d+)\s*分钟", desc)
        if m:
            n = min(59, max(1, int(m.group(1))))
            return f"*/{n} * * * *"
    if "每天" in desc or "daily" in desc.lower():
        return "0 9 * * *"
    return None
