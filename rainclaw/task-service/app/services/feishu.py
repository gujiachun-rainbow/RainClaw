"""Feishu (Lark) webhook push with rich card style."""
from typing import Any, Optional

import httpx
from loguru import logger


def _build_card(
    title: str,
    *,
    color: str = "blue",
    sections: list[dict[str, str]] | None = None,
    note: str = "",
) -> dict[str, Any]:
    header = {
        "title": {"tag": "plain_text", "content": title[:100]},
        "template": color,
    }
    elements: list[dict[str, Any]] = []

    if sections:
        for sec in sections:
            label = sec.get("label", "")
            value = sec.get("value", "")
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{label}**\n{value[:3000]}",
                },
            })
            elements.append({"tag": "hr"})

    if elements and elements[-1].get("tag") == "hr":
        elements.pop()

    if note:
        elements.append({
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": note[:200]},
            ],
        })

    return {
        "msg_type": "interactive",
        "card": {"header": header, "elements": elements},
    }


async def _post_card(webhook_url: str, card: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(webhook_url.strip(), json=card)
            if r.status_code != 200:
                logger.warning(f"Feishu webhook failed: {r.status_code} {r.text[:200]}")
                return False
            data = r.json()
            if data.get("code") not in (None, 0):
                logger.warning(f"Feishu webhook error: {data}")
                return False
            return True
    except Exception as e:
        logger.warning(f"Feishu webhook exception: {e}")
        return False


async def push_feishu_webhook(
    webhook_url: str,
    title: str,
    content: str,
    run_time: Optional[str] = None,
    extra: Optional[dict] = None,
) -> bool:
    if not webhook_url or not webhook_url.strip():
        return False
    sections = []
    if run_time:
        sections.append({"label": "⏱ 执行时间", "value": run_time})
    sections.append({"label": "📋 执行结果", "value": content})
    if extra:
        sections.append({"label": "📎 附加信息", "value": str(extra)[:500]})
    card = _build_card(title, color="blue", sections=sections)
    return await _post_card(webhook_url, card)


async def notify_task_started(
    webhook_url: str,
    task_name: str,
    run_time: str,
) -> bool:
    sections = [
        {"label": "⏱ 开始时间", "value": run_time},
    ]
    card = _build_card(
        f"🚀 任务开始执行：{task_name}",
        color="blue",
        sections=sections,
        note="RainClaw 定时任务",
    )
    return await _post_card(webhook_url, card)


async def notify_task_success(
    webhook_url: str,
    task_name: str,
    start_time: str,
    end_time: str,
    result: str,
) -> bool:
    display_result = result or "（无输出）"
    if len(display_result) > 500:
        display_result = display_result[:500] + "..."
    sections = [
        {"label": "⏱ 开始时间", "value": start_time},
        {"label": "⏱ 结束时间", "value": end_time},
        {"label": "📋 执行结果", "value": display_result},
    ]
    card = _build_card(
        f"✅ 任务执行成功：{task_name}",
        color="green",
        sections=sections,
        note="RainClaw 定时任务",
    )
    return await _post_card(webhook_url, card)


async def notify_task_failed(
    webhook_url: str,
    task_name: str,
    start_time: str,
    end_time: str,
    error: str,
) -> bool:
    display_error = error or "（未知错误）"
    if len(display_error) > 500:
        display_error = display_error[:500] + "..."
    sections = [
        {"label": "⏱ 开始时间", "value": start_time},
        {"label": "⏱ 结束时间", "value": end_time},
        {"label": "❌ 错误信息", "value": display_error},
    ]
    card = _build_card(
        f"❌ 任务执行失败：{task_name}",
        color="red",
        sections=sections,
        note="RainClaw 定时任务",
    )
    return await _post_card(webhook_url, card)


async def send_webhook_test(webhook_url: str, task_name: str) -> tuple[bool, str]:
    if not webhook_url or not webhook_url.strip():
        return False, "Webhook URL is empty"
    name = task_name or "Webhook"
    sections = [
        {"label": "🔔 验证信息", "value": "这是一条来自 RainClaw 的测试消息。\n如果您收到此消息，说明 Webhook 地址已配置正确。"},
    ]
    card = _build_card(
        f"🔗 Webhook 验证 — {name}",
        color="blue",
        sections=sections,
        note="RainClaw · Webhook 配置验证",
    )
    try:
        ok = await _post_card(webhook_url.strip(), card)
        if ok:
            return True, "验证成功，请到飞书群中查看测试消息"
        return False, "飞书返回错误，请检查 Webhook 地址是否有效"
    except Exception as e:
        return False, str(e)
