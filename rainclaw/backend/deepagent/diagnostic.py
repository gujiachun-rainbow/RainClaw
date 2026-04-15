"""
诊断模块 — 记录 Agent 每步 LLM 调用的完整上下文。

用于对比框架执行 vs 直接 LLM 调用之间的报告生成质量差异。
通过 LangChain callback 拦截每次 LLM 输入，记录：
  - 系统提示词完整内容
  - 每次 LLM 调用的完整消息列表（含截断后的工具结果）
  - 工具结果落盘前后的数据量对比
  - 上下文增长曲线（chars / tokens 随 LLM 调用次数变化）

启用：设置环境变量 DIAGNOSTIC_MODE=1
输出：{workspace}/_diagnostic/
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List, Optional

from langchain_core.callbacks import BaseCallbackHandler
from loguru import logger

DIAGNOSTIC_ENABLED = os.environ.get("DIAGNOSTIC_MODE", "").lower() in (
    "1", "true", "yes",
)


def _msg_to_dict(msg: Any) -> Dict[str, Any]:
    """将 LangChain message 序列化为可 JSON 化的 dict，保留完整内容。"""
    entry: Dict[str, Any] = {"type": type(msg).__name__}

    content = getattr(msg, "content", "")
    if isinstance(content, str):
        entry["content"] = content
        entry["content_chars"] = len(content)
    elif isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                btype = block.get("type", "")
                if btype == "text":
                    parts.append(block.get("text", ""))
                elif btype == "thinking":
                    t = block.get("thinking", "")
                    parts.append(f"[THINKING({len(t)} chars)]")
            elif isinstance(block, str):
                parts.append(block)
        entry["content"] = "\n".join(parts)
        entry["content_chars"] = len(entry["content"])
    else:
        entry["content"] = str(content)
        entry["content_chars"] = len(entry["content"])

    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        entry["tool_calls"] = []
        for tc in tool_calls:
            args = tc.get("args", {})
            args_json = (
                json.dumps(args, ensure_ascii=False, default=str)
                if isinstance(args, dict) else str(args)
            )
            entry["tool_calls"].append({
                "name": tc.get("name", "?"),
                "args_chars": len(args_json),
                "args": args,
            })

    if hasattr(msg, "tool_call_id"):
        entry["tool_call_id"] = getattr(msg, "tool_call_id", "")
    name = getattr(msg, "name", None)
    if name and hasattr(msg, "tool_call_id"):
        entry["tool_name"] = name

    return entry


class DiagnosticLogger:
    """Agent 执行诊断记录器 — 记录每步 LLM 实际看到的完整上下文。"""

    def __init__(self, workspace_dir: str, session_id: str):
        self.dir = os.path.join(workspace_dir, "_diagnostic")
        self.session_id = session_id
        self.llm_call_count = 0
        self.offload_events: List[Dict] = []
        self._call_summaries: List[Dict] = []
        self._start_time = time.time()
        os.makedirs(self.dir, exist_ok=True)
        os.chmod(self.dir, 0o777)
        logger.info(f"[Diagnostic] 诊断模式已启用 → {self.dir}")

    # ── 系统提示词 ──────────────────────────────────────────────

    def save_system_prompt(self, prompt: str):
        path = os.path.join(self.dir, "01_system_prompt.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(prompt)
        logger.info(f"[Diagnostic] 系统提示词已保存 ({len(prompt):,} chars)")

    # ── 初始输入（runner 发送给 agent 的消息列表） ────────────

    def save_initial_input(self, messages: List):
        path = os.path.join(self.dir, "02_initial_input.json")
        data = {
            "message_count": len(messages),
            "messages": [_msg_to_dict(m) for m in messages],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[Diagnostic] 初始输入已保存 ({len(messages)} messages)")

    # ── LLM 调用记录（每次模型被调用时触发） ────────────────

    def log_llm_call(self, messages: List):
        self.llm_call_count += 1
        idx = self.llm_call_count

        serialized = [_msg_to_dict(m) for m in messages]
        total_chars = sum(e.get("content_chars", 0) for e in serialized)

        type_counts: Dict[str, int] = {}
        for m in messages:
            t = type(m).__name__
            type_counts[t] = type_counts.get(t, 0) + 1

        summary = {
            "call_index": idx,
            "elapsed_s": round(time.time() - self._start_time, 2),
            "message_count": len(messages),
            "total_content_chars": total_chars,
            "estimated_tokens": total_chars * 2 // 3,
            "type_counts": type_counts,
        }
        self._call_summaries.append(summary)

        full_data = {**summary, "messages": serialized}

        if idx == 1:
            p = os.path.join(self.dir, "03_llm_call_first.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

        # 始终覆盖 last — 任务结束时即为报告生成步骤的上下文
        p = os.path.join(self.dir, "03_llm_call_last.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"[Diagnostic] LLM #{idx}: {len(messages)} msgs, "
            f"{total_chars:,} chars (~{total_chars * 2 // 3:,} tok), "
            f"types={type_counts}"
        )

    # ── 工具结果落盘事件 ──────────────────────────────────────

    def log_offload(
        self,
        tool_name: str,
        original_chars: int,
        summary_chars: int,
        file_path: str,
    ):
        evt = {
            "tool_name": tool_name,
            "original_chars": original_chars,
            "summary_chars": summary_chars,
            "lost_chars": original_chars - summary_chars,
            "lost_pct": round(
                (1 - summary_chars / max(original_chars, 1)) * 100, 1
            ),
            "file_path": file_path,
            "at_llm_call": self.llm_call_count,
        }
        self.offload_events.append(evt)
        logger.info(
            f"[Diagnostic] Offload {tool_name}: "
            f"{original_chars:,} → {summary_chars:,} chars "
            f"(-{evt['lost_pct']}%)"
        )

    # ── 最终诊断摘要 ──────────────────────────────────────────

    def save_summary(self):
        path = os.path.join(self.dir, "99_summary.json")
        total_lost = sum(e["lost_chars"] for e in self.offload_events)
        total_original = sum(e["original_chars"] for e in self.offload_events)

        growth = [
            {
                "call": s["call_index"],
                "chars": s["total_content_chars"],
                "tokens": s["estimated_tokens"],
                "msgs": s["message_count"],
            }
            for s in self._call_summaries
        ]

        summary = {
            "session_id": self.session_id,
            "total_duration_s": round(time.time() - self._start_time, 1),
            "total_llm_calls": self.llm_call_count,
            "context_growth_curve": growth,
            "offload_stats": {
                "total_events": len(self.offload_events),
                "total_original_chars": total_original,
                "total_lost_chars": total_lost,
                "overall_loss_pct": round(
                    total_lost / max(total_original, 1) * 100, 1
                ),
            },
            "offload_events": self.offload_events,
            "llm_calls_detail": self._call_summaries,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(
            f"[Diagnostic] 摘要已保存: {self.llm_call_count} 次 LLM 调用, "
            f"{len(self.offload_events)} 次落盘, "
            f"数据丢失 {total_lost:,} chars"
        )

    # ── LangChain Callback Handler ──────────────────────────

    def get_callback_handler(self) -> "DiagnosticCallbackHandler":
        return DiagnosticCallbackHandler(self)


class DiagnosticCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler，拦截每次 Chat Model 调用记录完整输入。

    on_chat_model_start 在模型被调用时触发，messages 参数包含模型
    实际看到的全部消息（经过 SummarizationMiddleware 压缩后的版本）。
    """

    def __init__(self, diag: DiagnosticLogger):
        super().__init__()
        self._diag = diag

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List],
        **kwargs: Any,
    ) -> None:
        try:
            flat = (
                messages[0]
                if messages and isinstance(messages[0], list)
                else messages
            )
            self._diag.log_llm_call(flat)
        except Exception:
            logger.warning("[Diagnostic] Failed to log LLM call", exc_info=True)
