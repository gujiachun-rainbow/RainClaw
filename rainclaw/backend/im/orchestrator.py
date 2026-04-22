from __future__ import annotations

import asyncio
import json
import time
import shortuuid
from typing import Any, Dict, Optional, List

from fastapi import HTTPException
from loguru import logger
from pymongo.errors import DuplicateKeyError

from backend.deepagent.runner import arun_science_task_stream
from backend.deepagent.sessions import async_get_science_session
from backend.im.base import IMAdapter, IMMessage, IMMessageFormatter, IMPlatform, IMResponse
from backend.im.command_handler import IMCommandHandler
from backend.im.session_manager import IMSessionManager
from backend.im.user_binding import IMUserBindingManager
from backend.mongodb.db import db

class IMServiceOrchestrator:
    def __init__(
        self,
        progress_mode: str = "text_multi",
        progress_interval_ms: int = 1200,
        realtime_events: Optional[list[str]] = None,
        max_message_length: int = 4000,
        progress_detail_level: str = "detailed",
    ):
        self.adapters: Dict[IMPlatform, IMAdapter] = {}
        self.formatters: Dict[IMPlatform, IMMessageFormatter] = {}
        self.session_manager = IMSessionManager()
        self.user_binding = IMUserBindingManager()
        self.command_handler = IMCommandHandler(self.session_manager)
        self.message_dedup_collection = "im_message_dedup"
        self.progress_mode = progress_mode if progress_mode in ("text_multi", "card_entity") else "text_multi"
        self.progress_interval_ms = max(300, min(progress_interval_ms, 10000))
        allowed_events = {"plan_update", "planning_message", "tool_call", "tool_result", "error"}
        self.realtime_events = {evt for evt in (realtime_events or []) if evt in allowed_events}
        self.max_message_length = max(500, min(int(max_message_length), 20000))
        self.progress_detail_level = progress_detail_level if progress_detail_level in ("compact", "detailed") else "detailed"

    def register_adapter(self, platform: IMPlatform, adapter: IMAdapter, formatter: IMMessageFormatter):
        self.adapters[platform] = adapter
        self.formatters[platform] = formatter
        logger.info(f"registered im adapter: {platform.value}")

    async def handle_webhook(self, platform: IMPlatform, request: Any) -> Any:
        adapter = self.adapters.get(platform)
        if not adapter:
            raise HTTPException(status_code=503, detail=f"adapter not configured: {platform.value}")
        if not await adapter.verify_webhook(request):
            raise HTTPException(status_code=401, detail="invalid signature")
        verification_response = await adapter.handle_url_verification(request)
        if verification_response:
            return verification_response
        message = await adapter.parse_message(request)
        if not message:
            return {"code": 0, "msg": "ok"}
        accepted = await self._mark_message_once(message)
        if not accepted:
            return {"code": 0, "msg": "ok"}
        asyncio.create_task(self._process_message(adapter, message))
        return {"code": 0, "msg": "ok"}

    async def handle_incoming_message(self, platform: IMPlatform, message: IMMessage) -> bool:
        adapter = self.adapters.get(platform)
        if not adapter:
            logger.error(f"adapter not configured: {platform.value}")
            return False
        accepted = await self._mark_message_once(message)
        if not accepted:
            logger.info(
                f"[IM] duplicate message ignored: platform={platform.value}, "
                f"message_id={message.message_id}, user={message.user.platform_user_id or '-'}"
            )
            return False
        logger.info(
            f"[IM] message accepted: platform={platform.value}, "
            f"message_id={message.message_id}, chat_id={message.chat.chat_id}, "
            f"user={message.user.platform_user_id or '-'}"
        )
        asyncio.create_task(self._process_message(adapter, message))
        return True

    async def _mark_message_once(self, message: IMMessage) -> bool:
        try:
            await db.get_collection(self.message_dedup_collection).insert_one(
                {
                    "_id": f"{message.platform.value}:{message.message_id}",
                    "platform": message.platform.value,
                    "message_id": message.message_id,
                    "created_at": message.timestamp,
                }
            )
            return True
        except DuplicateKeyError:
            return False

    async def _process_message(self, adapter: IMAdapter, message: IMMessage):
        formatter = self.formatters[message.platform]
        text = message.get_text().strip()
        logger.info(f"[IM] processing message: platform={message.platform.value}, message_id={message.message_id}, text_length={len(text)}, content_type={message.content_type}")
        if not text:
            logger.info(f"[IM] empty text ignored: platform={message.platform.value}, message_id={message.message_id}")
            return
        if message.chat.chat_type == "group" and not message.is_at_me and not text.startswith("/"):
            logger.info(
                f"[IM] group message ignored without mention: "
                f"platform={message.platform.value}, message_id={message.message_id}, chat_id={message.chat.chat_id}"
            )
            return
        try:
            binding = await self.user_binding.get_binding(
                platform=message.platform,
                platform_user_id=message.user.platform_user_id,
            )
            if not binding:
                logger.info(
                    f"[IM] no binding found: platform={message.platform.value}, "
                    f"user={message.user.platform_user_id or '-'}, message_id={message.message_id}"
                )
                response = self._create_binding_guide(
                    platform=message.platform,
                    platform_user_id=message.user.platform_user_id,
                )
                sent = await adapter.send_message(message.chat, response)
                logger.info(
                    f"[IM] binding guide sent={sent}: platform={message.platform.value}, "
                    f"user={message.user.platform_user_id or '-'}, message_id={message.message_id}"
                )
                return
            if text.startswith("/"):
                command_result = await self.command_handler.handle(
                    command=text,
                    message=message,
                    formatter=formatter,
                    science_user_id=binding.science_user_id,
                )
                if command_result.response:
                    sent = await adapter.send_message(message.chat, command_result.response)
                    logger.info(
                        f"[IM] command response sent={sent}: platform={message.platform.value}, "
                        f"user={message.user.platform_user_id or '-'}, message_id={message.message_id}"
                    )
                if command_result.should_stop:
                    return
            await adapter.send_typing_indicator(message.chat)
            session = await self.session_manager.get_or_create_session(
                platform=message.platform,
                platform_chat_id=message.chat.chat_id,
                user_id=binding.science_user_id,
            )
            # 更新科学会话的 events、latest_message、latest_message_at 字段
            science_session = await async_get_science_session(session.science_session_id)
            now = int(time.time())
            # 添加用户消息事件
            user_event = {
                "event": "message",
                "data": {
                    "event_id": shortuuid.uuid(),
                    "timestamp": now,
                    "content": text,
                    "role": "user",
                    "attachments": [],
                    "message_id": message.message_id
                }
            }
            events = getattr(science_session, "events", [])
            if not isinstance(events, list):
                events = []
                science_session.events = events
            events.append(user_event)
            # 更新最新消息字段
            science_session.latest_message = text
            science_session.latest_message_at = now
            # 生成会话标题（参考网页版逻辑）
            if text.strip() and not (getattr(science_session, "title", None) or "").strip():
                # 计算用户消息数量
                user_message_count = sum(1 for evt in events if evt.get("event") == "message" and evt.get("data", {}).get("role") == "user")
                if user_message_count <= 1:
                    try:
                        # 导入必要的模块
                        from backend.route.sessions import _generate_session_title
                        gen_title = await _generate_session_title(text)
                        if gen_title:
                            science_session.title = gen_title
                    except Exception as exc:
                        logger.warning("Title generation failed: %s", exc)
                        # 回退：使用消息的第一行或截断的消息
                        first_line = text.split("\n")[0].strip()
                        if first_line:
                            science_session.title = "[飞书]" + (first_line[:50] + "…") if len(first_line) > 50 else first_line
                        else:
                            science_session.title = "飞书会话"
            # 更新状态为运行中
            science_session.status = "running"
            await science_session.save()
            task_intro = text if len(text) <= 120 else f"{text[:117]}..."
            reply_to = message.message_id or None
            intro_sent = await adapter.send_message(
                message.chat,
                IMResponse(
                    content_type="text",
                    content=f"📌 任务介绍：{task_intro}",
                    reply_to_message_id=reply_to,
                ),
            )
            processing_sent = await adapter.send_message(
                message.chat,
                IMResponse(
                    content_type="text",
                    content="⏳ 已收到任务，正在处理...",
                    reply_to_message_id=reply_to,
                ),
            )
            logger.info(
                f"[IM] task ack sent: intro_sent={intro_sent}, processing_sent={processing_sent}, "
                f"platform={message.platform.value}, user={message.user.platform_user_id or '-'}, "
                f"session_id={session.science_session_id}, message_id={message.message_id}"
            )
            progress_state: Dict[str, Any] = {
                "started_monotonic": time.monotonic(),
                "tool_call_count": 0,
                "tool_result_count": 0,
                "plan_update_count": 0,
                "planning_message_count": 0,
                "error_count": 0,
            }
            on_progress = None
            if self.realtime_events:
                async def _on_progress(event_type: str, content: str, event_data: Optional[Dict[str, Any]] = None):
                    await self._send_progress_update(
                        adapter=adapter,
                        chat=message.chat,
                        progress_state=progress_state,
                        event_type=event_type,
                        content=content,
                        event_data=event_data or {},
                        reply_to_message_id=reply_to,
                    )

                on_progress = _on_progress
            response_text = await self._execute_ai_task(
                session_id=session.science_session_id,
                query=text,
                formatter=formatter,
                on_progress=on_progress,
                progress_state=progress_state,
                science_session=science_session,
            )
            # 更新科学会话的 events、latest_message、latest_message_at 字段，添加AI回复
            now = int(time.time())
            ai_event = {
                "event": "message",
                "data": {
                    "event_id": shortuuid.uuid(),
                    "timestamp": now,
                    "content": response_text,
                    "role": "assistant",
                    "attachments": []
                }
            }
            events = getattr(science_session, "events", [])
            if not isinstance(events, list):
                events = []
                science_session.events = events
            events.append(ai_event)
            # 更新最新消息字段为AI回复
            science_session.latest_message = response_text
            science_session.latest_message_at = now
            # 更新会话状态为已完成
            science_session.status = "completed"
            # 添加 done 事件
            done_event = {
                "event": "done",
                "data": {
                    "event_id": shortuuid.uuid(),
                    "timestamp": now,
                    "statistics": {
                        "tool_call_count": progress_state.get("tool_call_count", 0),
                        "total_duration_ms": int((time.time() - progress_state.get("started_monotonic", time.time())) * 1000),
                    },
                    "round_files": [],
                },
            }
            events = getattr(science_session, "events", [])
            if not isinstance(events, list):
                events = []
                science_session.events = events
            events.append(done_event)
            # 保存会话
            await science_session.save()
            if self.progress_mode == "card_entity":
                result_card = self._build_result_card(progress_state, response_text)
                logger.debug(f"[card_entity] 发送结果卡片, response_text 长度: {len(response_text)}")
                await adapter.send_message(
                    message.chat,
                    IMResponse(
                        content_type="card_entity",
                        content=json.dumps(result_card, ensure_ascii=False),
                        reply_to_message_id=reply_to,
                    ),
                )
                logger.debug(f"[card_entity] 结果卡片发送完成")
                if len(response_text) > 1600:
                    logger.debug(f"[card_entity] response_text 长度 {len(response_text)} > 1600, 需要拆分发送")
                    await self._send_markdown_chunks(
                        adapter=adapter,
                        chat=message.chat,
                        content=response_text,
                        reply_to_message_id=reply_to,
                    )
                    logger.debug(f"[card_entity] 拆分消息发送完成")
            else:
                await self._send_markdown_chunks(
                    adapter=adapter,
                    chat=message.chat,
                    content=response_text,
                    reply_to_message_id=reply_to,
                )
        except Exception as exc:
            logger.exception(f"process im message failed: {exc}")
            await adapter.send_message(
                message.chat,
                IMResponse(content_type="text", content="抱歉，处理消息时出错，请稍后重试。"),
            )

    async def _execute_ai_task(
        self,
        session_id: str,
        query: str,
        formatter: IMMessageFormatter,
        on_progress=None,
        progress_state: Optional[Dict[str, Any]] = None,
        science_session=None,
    ) -> str:
        logger.info(f"[IM] executing ai task: session_id={session_id}, query_length={len(query)}, query_preview={query[:100]}")
        session = science_session or await async_get_science_session(session_id)
        message_chunks: list[str] = []
        error_messages: list[str] = []
        last_tool_result: Optional[str] = None

        async for evt in arun_science_task_stream(session=session, query=query):
            event_type = evt.get("event")
            data = evt.get("data", {})
            self._record_progress_metrics(progress_state, event_type, data)
            if event_type == "thinking":
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "thinking",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "content": data.get("content", "")
                        }
                    })
                continue
            if event_type == "tool_call":
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "tool",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "tool_call_id": data.get("tool_call_id", shortuuid.uuid()),
                            "name": data.get("function", ""),
                            "status": "calling",
                            "function": data.get("function", ""),
                            "args": data.get("args", {})
                        }
                    })
                if on_progress and event_type in self.realtime_events:
                    text = formatter.format_tool_call(data.get("function", ""), data.get("args", {}))
                    await on_progress("tool_call", text, data)
                continue
            if event_type == "tool_result":
                content = data.get("content")
                if isinstance(content, (dict, list)):
                    last_tool_result = json.dumps(content, ensure_ascii=False, indent=2)
                else:
                    last_tool_result = str(content)

                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "tool",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "tool_call_id": data.get("tool_call_id", ""),
                            "name": data.get("function", ""),
                            "status": "called",
                            "function": data.get("function", ""),
                            "content": content,
                            "duration_ms": data.get("duration_ms")
                        }
                    })
                if on_progress and event_type in self.realtime_events:
                    success = str(data.get("status", "success")).lower() != "error"
                    text = formatter.format_tool_result(data.get("function", ""), success=success)
                    await on_progress("tool_result", text, data)
                continue
            if event_type == "planning_message":
                content = data.get("content")
                if content:
                    message_chunks.append(str(content))
                if on_progress and event_type in self.realtime_events and content:
                    text = self._normalize_realtime_content("planning_message", str(content))
                    await on_progress("planning_message", text, data)
                continue
            if event_type == "step_start":
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "step",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "status": "running",
                            "id": str(data.get("step", {}).get("id", "S1")),
                            "description": str(data.get("step", {}).get("content", ""))
                        },
                        "id": shortuuid.uuid(),
                        "created_at": int(time.time()),
                    })
                continue
            if event_type == "step_end":
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "step",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "status": "completed",
                            "id": str(data.get("step_id", "S1")),
                            "description": ""
                        },
                        "id": shortuuid.uuid(),
                        "created_at": int(time.time()),
                    })
                continue
            if event_type == "plan_update":
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    plan = data.get("plan") or []
                    if isinstance(plan, list):
                        events.append({
                            "event": "plan",
                            "data": {
                                "event_id": shortuuid.uuid(),
                                "timestamp": int(time.time()),
                                "steps": self._map_plan_to_steps(plan)
                            },
                            "id": shortuuid.uuid(),
                            "created_at": int(time.time()),
                        })
                if on_progress and event_type in self.realtime_events:
                    plan_steps = data.get("plan", [])
                    text = formatter.format_plan(plan_steps) if plan_steps else "📋 执行计划已更新"
                    await on_progress("plan_update", text, data)
                continue
            if event_type == "message_chunk":
                content = data.get("content")
                if content:
                    message_chunks.append(str(content))
                continue
            if event_type == "error":
                error_text = formatter.format_error(data.get("message", "未知错误"))
                error_messages.append(error_text)
                if science_session:
                    events = getattr(science_session, "events", [])
                    if not isinstance(events, list):
                        events = []
                        science_session.events = events
                    events.append({
                        "event": "error",
                        "data": {
                            "event_id": shortuuid.uuid(),
                            "timestamp": int(time.time()),
                            "error": data.get("message", "未知错误")
                        }
                    })
                if on_progress and event_type in self.realtime_events:
                    await on_progress("error", self._normalize_realtime_content("error", error_text), data)
                continue
            if event_type == "statistics":
                continue
        if message_chunks:
            result = self._merge_message_chunks(message_chunks)
        elif error_messages:
            result = "\n\n".join(error_messages)
        elif last_tool_result:
            result = f"任务已完成。结果如下：\n{last_tool_result}"
        else:
            result = "任务已完成。"
        return result

    async def _send_progress_update(
        self,
        adapter: IMAdapter,
        chat,
        progress_state: Dict[str, Any],
        event_type: str,
        content: str,
        event_data: Dict[str, Any],
        reply_to_message_id: Optional[str] = None,
    ):
        now = time.monotonic()
        progress_state.setdefault("started_monotonic", now)
        progress_changed = self._apply_progress_step(progress_state, event_type, content, event_data)
        if not progress_changed:
            return
        progress_state["latest_step"] = content[:120]
        interval_seconds = self.progress_interval_ms / 1000
        last_push = float(progress_state.get("last_push_monotonic") or 0)
        if (
            self._should_throttle_event(event_type)
            and now - last_push < interval_seconds
            and not self._should_force_send(event_type, event_data)
        ):
            return
        progress_state["last_push_monotonic"] = now

        if self.progress_mode == "card_entity":
            card_payload = self._build_progress_card(progress_state)
            response = IMResponse(
                content_type="card_entity",
                content=json.dumps(card_payload, ensure_ascii=False),
                reply_to_message_id=reply_to_message_id,
            )
            progress_message_id = str(progress_state.get("progress_message_id") or "")
            if progress_message_id:
                updated = await adapter.update_message(progress_message_id, response)
                if updated:
                    return
            send_with_id = getattr(adapter, "send_message_with_id", None)
            if callable(send_with_id):
                ok, message_id = await send_with_id(chat, response)
                if ok and message_id:
                    progress_state["progress_message_id"] = message_id
                return
            await adapter.send_message(chat, response)
            return
        await adapter.send_message(
            chat,
            IMResponse(content_type="text", content=content, reply_to_message_id=reply_to_message_id),
        )

    def _build_progress_card(self, progress_state: Dict[str, Any]) -> Dict[str, Any]:
        steps = progress_state.get("steps", [])
        step_lines: list[str] = []
        for step in steps[-8:]:
            icon = self._step_icon(str(step.get("status", "pending")))
            title = str(step.get("title", "")).strip() or "处理中"
            detail = str(step.get("detail", "")).strip()
            if detail:
                step_lines.append(f"{icon} {title}  \n{detail}")
            else:
                step_lines.append(f"{icon} {title}")
        step_content = "\n".join(step_lines) if step_lines else "🔄 正在初始化执行流程"
        return {
            "schema": "2.0",
            "config": {"update_multi": True},
            "body": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {"tag": "lark_md", "content": f"{step_content}"},
                    },
                ],
            },
        }

    def _build_result_card(self, progress_state: Dict[str, Any], result_text: str) -> Dict[str, Any]:
        tool_call_count = max(
            int(progress_state.get("tool_call_count", 0)),
            int(progress_state.get("statistics_tool_call_count", 0)),
        )
        tool_result_count = int(progress_state.get("tool_result_count", 0))
        plan_update_count = int(progress_state.get("plan_update_count", 0))
        planning_message_count = int(progress_state.get("planning_message_count", 0))
        error_count = int(progress_state.get("error_count", 0))
        steps = progress_state.get("steps", [])
        failed_count = sum(1 for step in steps if str(step.get("status", "")) == "failed")
        elapsed_seconds = self._resolve_elapsed_text(progress_state)
        preview = result_text if len(result_text) <= 1600 else "结果较长，已拆分为后续消息发送。"
        key_points = self._extract_key_points(result_text)
        failed_summary = self._build_failed_steps_summary(steps)
        elements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**执行统计**\n"
                        f"• 工具调用：`{tool_call_count}` 次\n"
                        f"• 工具完成：`{tool_result_count}` 次\n"
                        f"• 计划更新：`{plan_update_count}` 次\n"
                        f"• 计划说明：`{planning_message_count}` 条\n"
                        f"• 错误事件：`{error_count}` 条\n"
                        f"• 失败步骤：`{failed_count}` 个\n"
                        f"• 总耗时：`{elapsed_seconds}`"
                    ),
                },
            },
        ]
        if key_points:
            elements.extend(
                [
                    {"tag": "hr"},
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"\n**关键结论**\n{key_points}"}},
                ]
            )
        if failed_summary:
            elements.extend(
                [
                    {"tag": "hr"},
                    {"tag": "div", "text": {"tag": "lark_md", "content": f"\n**失败步骤摘要**\n{failed_summary}"}},
                ]
            )
        elements.extend(
            [
                {"tag": "hr"},
                {"tag": "div", "text": {"tag": "lark_md", "content": f"\n**最终结果**\n{preview}"}},
            ]
        )
        return {
            "schema": "2.0",
            "config": {"update_multi": True},
            "body": {"elements": elements},
        }

    async def _send_markdown_chunks(
        self,
        adapter: IMAdapter,
        chat: Any,
        content: str,
        reply_to_message_id: Optional[str] = None,
    ) -> None:
        safe_chunk_length = max(500, self.max_message_length - 120)
        chunks = self._split_message_chunks(content, safe_chunk_length)
        total = len(chunks)
        logger.debug(f"[markdown_chunks] 内容总长度: {len(content)}, 拆分为 {total} 个分片, 单分片上限: {safe_chunk_length}")
        for idx, chunk in enumerate(chunks, start=1):
            payload = chunk
            logger.debug(f"[markdown_chunks] 发送分片 {idx}/{total}, 分片长度: {len(payload)}")
            await adapter.send_message(
                chat,
                IMResponse(
                    content_type="markdown",
                    content=payload,
                    reply_to_message_id=reply_to_message_id,
                ),
            )
        logger.debug(f"[markdown_chunks] 所有分片发送完成, 共 {total} 个")

    def _split_message_chunks(self, text: str, max_length: int) -> list[str]:
        raw = str(text or "")
        if not raw:
            return [""]
        limit = max(500, int(max_length))
        if len(raw) <= limit:
            return [raw]
        chunks: list[str] = []
        start = 0
        while start < len(raw):
            end = min(start + limit, len(raw))
            if end < len(raw):
                split_candidates = [
                    raw.rfind("\n\n", start, end),
                    raw.rfind("\n", start, end),
                ]
                for split_at in split_candidates:
                    if split_at > start + int(limit * 0.55):
                        end = split_at
                        break
            piece = raw[start:end]
            if piece.count("```") % 2 == 1 and end < len(raw):
                next_fence = raw.find("```", end)
                if next_fence != -1 and next_fence - start <= limit + 400:
                    end = next_fence + 3
                    piece = raw[start:end]
            piece = piece.rstrip("\n")
            if piece:
                chunks.append(piece)
            start = end
            while start < len(raw) and raw[start] == "\n":
                start += 1
        return chunks if chunks else [raw[:limit]]

    def _merge_message_chunks(self, chunks: list[str]) -> str:
        merged: list[str] = []
        for item in chunks:
            chunk = str(item or "")
            if not chunk.strip():
                continue
            if merged and merged[-1].strip() == chunk.strip():
                continue
            if not merged:
                merged.append(chunk)
                continue
            if merged[-1].endswith("\n") or chunk.startswith("\n"):
                merged[-1] = f"{merged[-1]}{chunk}"
            else:
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
        if not merged:
            return ""
        return "".join(merged)

    def _extract_key_points(self, result_text: str) -> str:
        lines = [line.strip() for line in str(result_text or "").splitlines() if line.strip()]
        if not lines:
            return ""
        bullet_lines = [line for line in lines if line.startswith(("-", "•", "*", "1.", "2.", "3."))]
        selected = bullet_lines[:3] if bullet_lines else lines[:3]
        normalized: list[str] = []
        for line in selected:
            if line.startswith(("-", "•", "*")):
                normalized.append(line)
            else:
                normalized.append(f"• {line[:140]}")
        return "\n".join(normalized)

    def _build_failed_steps_summary(self, steps: list[Dict[str, Any]]) -> str:
        failed_steps = [step for step in steps if str(step.get("status", "")) == "failed"]
        if not failed_steps:
            return ""
        lines: list[str] = []
        for step in failed_steps[-5:]:
            title = str(step.get("title", "")).strip() or "失败步骤"
            detail = str(step.get("detail", "")).strip()
            if detail:
                lines.append(f"• {title}：{detail[:120]}")
            else:
                lines.append(f"• {title}")
        return "\n".join(lines)

    def _apply_progress_step(
        self,
        progress_state: Dict[str, Any],
        event_type: str,
        content: str,
        event_data: Dict[str, Any],
    ) -> bool:
        steps = progress_state.setdefault("steps", [])
        pending_tools = progress_state.setdefault("pending_tools", {})
        changed = False
        if event_type == "tool_call":
            function_name = str(event_data.get("function", "") or "tool")
            args = self._summarize_tool_args(event_data.get("args"))
            step = {
                "status": "in_progress",
                "title": f"工具调用：{function_name}",
                "detail": args if self.progress_detail_level == "detailed" else "",
                "started_monotonic": float(time.monotonic()),
            }
            steps.append(step)
            pending_steps = pending_tools.setdefault(function_name, [])
            pending_steps.append(step)
            changed = True
        elif event_type == "tool_result":
            function_name = str(event_data.get("function", "") or "tool")
            status = str(event_data.get("status", "success")).lower()
            step_status = "completed" if status != "error" else "failed"
            pending_steps = pending_tools.get(function_name) or []
            step = pending_steps.pop(0) if pending_steps else None
            if not pending_steps and function_name in pending_tools:
                pending_tools.pop(function_name, None)
            elapsed = None
            if step:
                started = float(step.get("started_monotonic") or 0)
                if started > 0:
                    elapsed = max(0.0, time.monotonic() - started)
            detail = self._summarize_tool_result(event_data, elapsed_seconds=elapsed)
            if step:
                step["status"] = step_status
                step["detail"] = detail
                changed = True
            else:
                steps.append({"status": step_status, "title": f"工具结果：{function_name}", "detail": detail})
                changed = True
        elif event_type == "planning_message":
            detail = content[:160] if self.progress_detail_level == "detailed" else ""
            steps.append({"status": "completed", "title": "规划说明", "detail": detail})
            changed = True
        elif event_type == "plan_update":
            plan_steps = event_data.get("plan")
            if not isinstance(plan_steps, list) or not plan_steps:
                return False
            plan_hash = str(hash(str(event_data.get("plan"))))
            last_hash = str(progress_state.get("last_plan_hash", ""))
            if plan_hash == last_hash:
                return False
            progress_state["last_plan_hash"] = plan_hash
            existing_plan_steps: Dict[str, Dict[str, Any]] = {}
            for step in steps:
                if str(step.get("source", "")) != "plan":
                    continue
                key = str(step.get("plan_step_key", "")).strip()
                if key:
                    existing_plan_steps[key] = step
            status_map = {
                "completed": "completed",
                "in_progress": "in_progress",
                "running": "in_progress",
                "failed": "failed",
                "pending": "pending",
            }
            for plan_step in plan_steps:
                if not isinstance(plan_step, dict):
                    continue
                title = str(plan_step.get("description") or plan_step.get("content") or "").strip()
                if not title:
                    continue
                step_id = str(plan_step.get("id") or "").strip()
                step_key = step_id or title
                mapped_status = status_map.get(str(plan_step.get("status") or "pending").strip().lower(), "pending")
                detail = ""
                target = existing_plan_steps.get(step_key)
                if target:
                    target["status"] = mapped_status
                    target["title"] = title
                    target["detail"] = detail
                else:
                    step_item = {
                        "status": mapped_status,
                        "title": title,
                        "detail": detail,
                        "source": "plan",
                        "plan_step_key": step_key,
                    }
                    steps.append(step_item)
                    existing_plan_steps[step_key] = step_item
                changed = True
        elif event_type == "error":
            detail = content[:160] if self.progress_detail_level == "detailed" else ""
            steps.append({"status": "failed", "title": "执行错误", "detail": detail})
            changed = True
        if len(steps) > 12:
            del steps[:-12]
            changed = True
        return changed

    def _summarize_tool_args(self, args: Any) -> str:
        if args is None:
            return "参数：无"
        if isinstance(args, dict):
            keys = [str(key) for key in args.keys()][:4]
            if not keys:
                return "参数：无"
            return f"参数：{', '.join(keys)}"
        if isinstance(args, list):
            return f"参数：列表({len(args)})"
        return f"参数：{str(args)[:80]}"

    def _summarize_tool_result(self, event_data: Dict[str, Any], elapsed_seconds: Optional[float] = None) -> str:
        if self.progress_detail_level != "detailed":
            status = str(event_data.get("status", "success")).lower()
            summary = "成功" if status != "error" else "失败"
            return f"结果：{summary}"
        status = str(event_data.get("status", "success")).lower()
        content = event_data.get("content")
        summary = "成功" if status != "error" else "失败"
        duration_text = self._extract_duration_text(event_data, elapsed_seconds)
        if isinstance(content, str) and content.strip():
            return f"结果：{summary}，{duration_text}，{content.strip()[:90]}"
        if isinstance(content, dict):
            return f"结果：{summary}，{duration_text}，返回字段 {len(content)} 个"
        if isinstance(content, list):
            return f"结果：{summary}，{duration_text}，返回列表 {len(content)} 项"
        return f"结果：{summary}，{duration_text}"

    def _extract_duration_text(self, event_data: Dict[str, Any], elapsed_seconds: Optional[float]) -> str:
        duration_candidates = [
            event_data.get("duration_ms"),
            event_data.get("cost_ms"),
            event_data.get("duration"),
        ]
        for candidate in duration_candidates:
            if isinstance(candidate, (int, float)):
                value = float(candidate)
                if "ms" in str(candidate).lower() or candidate == event_data.get("duration_ms") or candidate == event_data.get("cost_ms"):
                    return f"耗时 {max(value, 0.0) / 1000:.1f}s"
                return f"耗时 {max(value, 0.0):.1f}s"
        if elapsed_seconds is not None:
            return f"耗时 {max(elapsed_seconds, 0.0):.1f}s"
        return "耗时 -"

    def _format_elapsed_seconds(self, elapsed_seconds: float) -> str:
        total = int(max(0, elapsed_seconds))
        minutes, seconds = divmod(total, 60)
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def _resolve_elapsed_text(self, progress_state: Dict[str, Any]) -> str:
        total_duration_ms = progress_state.get("total_duration_ms")
        if isinstance(total_duration_ms, (int, float)) and total_duration_ms >= 0:
            return self._format_elapsed_seconds(float(total_duration_ms) / 1000)
        started = float(progress_state.get("started_monotonic") or time.monotonic())
        return self._format_elapsed_seconds(max(0.0, time.monotonic() - started))

    def _record_progress_metrics(
        self,
        progress_state: Optional[Dict[str, Any]],
        event_type: str,
        event_data: Dict[str, Any],
    ) -> None:
        if progress_state is None:
            return
        if event_type == "tool_call":
            progress_state["tool_call_count"] = int(progress_state.get("tool_call_count", 0)) + 1
        elif event_type == "tool_result":
            progress_state["tool_result_count"] = int(progress_state.get("tool_result_count", 0)) + 1
        elif event_type == "plan_update":
            progress_state["plan_update_count"] = int(progress_state.get("plan_update_count", 0)) + 1
        elif event_type == "planning_message":
            progress_state["planning_message_count"] = int(progress_state.get("planning_message_count", 0)) + 1
        elif event_type == "error":
            progress_state["error_count"] = int(progress_state.get("error_count", 0)) + 1
        elif event_type == "statistics":
            tool_calls = event_data.get("tool_call_count")
            total_duration_ms = event_data.get("total_duration_ms")
            if isinstance(tool_calls, (int, float)):
                progress_state["statistics_tool_call_count"] = int(tool_calls)
            if isinstance(total_duration_ms, (int, float)):
                progress_state["total_duration_ms"] = float(total_duration_ms)

    def _should_force_send(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        if event_type == "error":
            return True
        if event_type != "plan_update":
            return False
        plan_steps = event_data.get("plan")
        if not isinstance(plan_steps, list) or not plan_steps:
            return False
        statuses = [str(step.get("status", "")) for step in plan_steps if isinstance(step, dict)]
        if not statuses:
            return False
        return all(status == "completed" for status in statuses)

    def _should_throttle_event(self, event_type: str) -> bool:
        return event_type in ("plan_update", "planning_message")

    def _normalize_realtime_content(self, event_type: str, content: str) -> str:
        text = str(content or "").strip()
        if not text:
            return ""
        if event_type == "planning_message":
            return text if len(text) <= 220 else text[:217] + "..."
        if event_type == "error":
            return text if len(text) <= 260 else text[:257] + "..."
        return text

    def _step_icon(self, status: str) -> str:
        return {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "failed": "❌",
        }.get(status, "⏳")

    def _map_plan_to_steps(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        def _map_status(status: str) -> str:
            status = (status or "pending").strip()
            if status in {"in_progress", "running"}:
                return "running"
            if status == "completed":
                return "completed"
            if status in {"blocked", "failed"}:
                return "failed"
            return "pending"

        return [
            {
                "event_id": shortuuid.uuid(),
                "timestamp": int(time.time()),
                "status": _map_status(str(step.get("status") or "pending")),
                "id": str(step.get("id") or ""),
                "description": str(step.get("content") or ""),
                "tools": step.get("tools") if isinstance(step.get("tools"), list) else [],
            }
            for step in plan
        ]

    def _create_binding_guide(self, platform: IMPlatform, platform_user_id: str) -> IMResponse:
        platform_name = {
            IMPlatform.LARK: "飞书",
            IMPlatform.WECOM: "企业微信",
            IMPlatform.DINGTALK: "钉钉",
            IMPlatform.SLACK: "Slack",
        }.get(platform, platform.value)
        pair_cmd = f"/bind_lark {platform_user_id}" if platform == IMPlatform.LARK else f"/bind_{platform.value} {platform_user_id}"
        content = (
            "👋 欢迎使用 RainClaw\n\n"
            f"当前 {platform_name} 账号未绑定，请先在 Web 端完成绑定：\n"
            "我的 -> IM -> 飞书账号绑定 -> 粘贴下面整条配对命令，或仅输入飞书 open_id。\n\n"
            f"你的 {platform_name} 用户ID：`{platform_user_id}`\n"
            "绑定完成后即可在 IM 中直接对话。"
        )
        return IMResponse(content_type="markdown", content=content)
