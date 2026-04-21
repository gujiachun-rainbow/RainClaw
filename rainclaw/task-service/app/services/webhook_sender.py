"""Multi-platform webhook sender (Feishu, DingTalk, WeCom)."""
from typing import Tuple

import httpx
from loguru import logger


# ==================== Feishu ====================

def _feishu_card(title: str, content: str, *, color: str = "blue") -> dict:
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": title[:100]},
                "template": color,
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content[:4000]}},
                {"tag": "hr"},
                {"tag": "note", "elements": [{"tag": "plain_text", "content": "RainClaw 定时任务"}]},
            ],
        },
    }


async def _send_feishu(url: str, title: str, content: str) -> bool:
    is_success = "成功" in title
    is_fail = "失败" in title
    color = "green" if is_success else ("red" if is_fail else "blue")
    body = _feishu_card(title, content, color=color)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=body)
        if r.status_code != 200:
            logger.warning(f"Feishu webhook failed: {r.status_code} {r.text[:200]}")
            return False
        data = r.json()
        return data.get("code") in (None, 0)


# ==================== DingTalk ====================

def _dingtalk_actioncard(title: str, content: str) -> dict:
    """Build a DingTalk ActionCard for richer display."""
    is_success = "成功" in title
    is_fail = "失败" in title
    icon = "✅" if is_success else ("❌" if is_fail else "🔔")
    color = "#07C160" if is_success else ("#FF4D4F" if is_fail else "#1890FF")

    md = (
        f"## <font color=\"{color}\">{icon} {title}</font>\n\n"
        f"---\n\n"
        f"{content[:4000]}\n\n"
        f"---\n\n"
        f"> RainClaw 定时任务"
    )
    return {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title[:100],
            "text": md,
            "hideAvatar": "0",
            "btnOrientation": "0",
        },
    }


async def _send_dingtalk(url: str, title: str, content: str) -> bool:
    body = _dingtalk_actioncard(title, content)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=body)
        if r.status_code != 200:
            logger.warning(f"DingTalk webhook failed: {r.status_code} {r.text[:200]}")
            return False
        data = r.json()
        return data.get("errcode") == 0


# ==================== WeCom ====================

def _wecom_markdown(title: str, content: str) -> dict:
    """Build a WeCom markdown message with styled layout."""
    is_success = "成功" in title
    is_fail = "失败" in title
    icon = "✅" if is_success else ("❌" if is_fail else "🔔")
    color = "info" if is_success else ("warning" if is_fail else "comment")

    md = (
        f"### {icon} {title}\n"
        f"\n"
        f"{content[:4000]}\n"
        f"\n"
        f"> <font color=\"{color}\">RainClaw 定时任务</font>"
    )
    return {
        "msgtype": "markdown",
        "markdown": {"content": md},
    }


async def _send_wecom(url: str, title: str, content: str) -> bool:
    body = _wecom_markdown(title, content)
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(url, json=body)
        if r.status_code != 200:
            logger.warning(f"WeCom webhook failed: {r.status_code} {r.text[:200]}")
            return False
        data = r.json()
        return data.get("errcode") == 0


# ==================== Dispatcher ====================

_SENDERS = {
    "feishu": _send_feishu,
    "dingtalk": _send_dingtalk,
    "wecom": _send_wecom,
}


async def send_webhook(webhook_type: str, url: str, title: str, content: str) -> bool:
    sender = _SENDERS.get(webhook_type, _send_feishu)
    try:
        return await sender(url, title, content)
    except Exception as e:
        logger.warning(f"Webhook send failed ({webhook_type}): {e}")
        return False


async def send_test_message(webhook_type: str, webhook_url: str, webhook_name: str) -> Tuple[bool, str]:
    if not webhook_url or not webhook_url.strip():
        return False, "Webhook URL is empty"
    name = webhook_name or "Webhook"
    title = f"🔗 Webhook 验证 — {name}"
    content = (
        "**🔔 验证信息**\n"
        "这是一条来自 RainClaw 的测试消息。\n\n"
        "如果您收到此消息，说明 Webhook 地址已配置正确。"
    )
    try:
        ok = await send_webhook(webhook_type, webhook_url.strip(), title, content)
        if ok:
            return True, "验证成功，请查看对应群中的测试消息"
        return False, "发送失败，请检查 Webhook 地址是否有效"
    except Exception as e:
        return False, str(e)
