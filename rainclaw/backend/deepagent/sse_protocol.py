"""
SSE 协议管理器 — 工具注册表、事件类型、图标分类。

参考 sample/sse_protocol_manager.py 实现，适配 RainClaw 实际工具集。
为后端事件流提供统一的工具元数据（图标、分类、描述），供前端展示。
"""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


# ───────────────────────────────────────────────────────────────────
# 枚举定义
# ───────────────────────────────────────────────────────────────────

class EventType(str, Enum):
    """SSE 事件类型"""
    MESSAGE = "message"
    THINKING = "thinking"
    PLAN = "plan"
    TOOL = "tool"
    STEP = "step"
    AGENT = "agent"
    ERROR = "error"
    DONE = "done"


class ToolCategory(str, Enum):
    """工具类别"""
    SEARCH = "search"
    FILESYSTEM = "filesystem"
    EXECUTION = "execution"
    NETWORK = "network"
    DATA = "data"
    SKILL = "skill"
    SYSTEM = "system"
    CUSTOM = "custom"


# ───────────────────────────────────────────────────────────────────
# 工具定义
# ───────────────────────────────────────────────────────────────────

class ToolMeta:
    """工具元数据"""
    __slots__ = ("name", "category", "icon", "description")

    def __init__(self, name: str, category: ToolCategory, icon: str, description: str):
        self.name = name
        self.category = category
        self.icon = icon
        self.description = description

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "category": self.category.value,
            "icon": self.icon,
            "description": self.description,
        }


# ───────────────────────────────────────────────────────────────────
# 工具注册表
# ───────────────────────────────────────────────────────────────────

class ToolRegistry:
    """工具注册表 — 维护所有已知工具的元数据（图标、分类、描述）"""

    def __init__(self):
        self._tools: Dict[str, ToolMeta] = {}
        self._extra_meta: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_tools()

    def _initialize_default_tools(self):
        """注册 RainClaw 内置工具"""

        # ── 搜索类 ──
        self.register(ToolMeta("web_search", ToolCategory.SEARCH, "🔍", "Web Search"))
        self.register(ToolMeta("web_crawl", ToolCategory.NETWORK, "🌐", "Web Crawl"))

        # ── Terminal 类（MCP sandbox） ──
        self.register(ToolMeta("terminal_execute", ToolCategory.EXECUTION, "⚡", "Execute Command"))
        self.register(ToolMeta("terminal_session", ToolCategory.EXECUTION, "⚡", "Terminal Session"))
        self.register(ToolMeta("terminal_kill", ToolCategory.EXECUTION, "🛑", "Kill Process"))
        # 兼容旧名称
        self.register(ToolMeta("sandbox_exec", ToolCategory.EXECUTION, "⚡", "Execute Command"))
        self.register(ToolMeta("execute", ToolCategory.EXECUTION, "⚡", "Execute Command"))

        # ── 文件系统类（MCP sandbox） ──
        self.register(ToolMeta("file_read", ToolCategory.FILESYSTEM, "📖", "Read File"))
        self.register(ToolMeta("file_write", ToolCategory.FILESYSTEM, "✏️", "Write File"))
        self.register(ToolMeta("file_list", ToolCategory.FILESYSTEM, "📂", "List Files"))
        self.register(ToolMeta("file_search", ToolCategory.SEARCH, "🔎", "Search Files"))
        self.register(ToolMeta("file_replace", ToolCategory.FILESYSTEM, "✏️", "Replace in File"))
        # 兼容旧名称
        self.register(ToolMeta("sandbox_read_file", ToolCategory.FILESYSTEM, "📖", "Read File"))
        self.register(ToolMeta("sandbox_write_file", ToolCategory.FILESYSTEM, "✏️", "Write File"))
        self.register(ToolMeta("sandbox_find_files", ToolCategory.FILESYSTEM, "📂", "Find Files"))
        self.register(ToolMeta("read_file", ToolCategory.FILESYSTEM, "📖", "Read File"))
        self.register(ToolMeta("write_file", ToolCategory.FILESYSTEM, "✏️", "Write File"))
        self.register(ToolMeta("edit_file", ToolCategory.FILESYSTEM, "✏️", "Edit File"))
        self.register(ToolMeta("find_files", ToolCategory.FILESYSTEM, "📂", "Find Files"))
        self.register(ToolMeta("ls", ToolCategory.FILESYSTEM, "📂", "List Files"))
        self.register(ToolMeta("grep", ToolCategory.SEARCH, "🔎", "Search Text"))
        self.register(ToolMeta("write", ToolCategory.FILESYSTEM, "✏️", "Write File"))

        # ── 浏览器类（MCP sandbox） ──
        self.register(ToolMeta("browser_navigate", ToolCategory.NETWORK, "🌐", "Navigate URL"))
        self.register(ToolMeta("browser_screenshot", ToolCategory.NETWORK, "📸", "Screenshot"))
        self.register(ToolMeta("browser_extract", ToolCategory.NETWORK, "🌐", "Extract Page"))
        self.register(ToolMeta("browser_click", ToolCategory.NETWORK, "🖱️", "Click Element"))
        self.register(ToolMeta("browser_type", ToolCategory.NETWORK, "⌨️", "Type Text"))
        self.register(ToolMeta("browser_close", ToolCategory.NETWORK, "🌐", "Close Browser"))
        self.register(ToolMeta("browser_get_markdown", ToolCategory.NETWORK, "🌐", "Get Markdown"))
        self.register(ToolMeta("browser_get_text", ToolCategory.NETWORK, "🌐", "Get Page Text"))
        self.register(ToolMeta("browser_read_links", ToolCategory.NETWORK, "🔗", "Read Links"))
        self.register(ToolMeta("browser_tab_list", ToolCategory.NETWORK, "🌐", "List Tabs"))
        self.register(ToolMeta("browser_switch_tab", ToolCategory.NETWORK, "🌐", "Switch Tab"))
        self.register(ToolMeta("browser_go_back", ToolCategory.NETWORK, "🌐", "Go Back"))
        self.register(ToolMeta("browser_go_forward", ToolCategory.NETWORK, "🌐", "Go Forward"))
        self.register(ToolMeta("browser_hover", ToolCategory.NETWORK, "🌐", "Hover Element"))
        self.register(ToolMeta("browser_select", ToolCategory.NETWORK, "🌐", "Select Element"))
        self.register(ToolMeta("browser_form_input_fill", ToolCategory.NETWORK, "🌐", "Fill Form"))
        self.register(ToolMeta("browser_get_clickable_elements", ToolCategory.NETWORK, "🌐", "Get Elements"))
        self.register(ToolMeta("browser_get_download_list", ToolCategory.NETWORK, "📥", "Downloads"))

        # ── 文档处理类（MCP sandbox） ──
        self.register(ToolMeta("markitdown_extract", ToolCategory.DATA, "📄", "Extract Document"))
        self.register(ToolMeta("markitdown_convert", ToolCategory.DATA, "📄", "Convert to Markdown"))

        # ── MCP Sandbox 实际工具名 ──
        self.register(ToolMeta("sandbox_execute_bash", ToolCategory.EXECUTION, "⚡", "Execute Bash"))
        self.register(ToolMeta("sandbox_execute_code", ToolCategory.EXECUTION, "🐍", "Execute Code"))
        self.register(ToolMeta("sandbox_file_operations", ToolCategory.FILESYSTEM, "📂", "File Operations"))
        self.register(ToolMeta("sandbox_str_replace_editor", ToolCategory.FILESYSTEM, "✏️", "Edit File"))
        self.register(ToolMeta("sandbox_get_context", ToolCategory.SYSTEM, "📋", "Get Context"))
        self.register(ToolMeta("sandbox_get_packages", ToolCategory.SYSTEM, "📦", "Get Packages"))
        self.register(ToolMeta("sandbox_convert_to_markdown", ToolCategory.DATA, "📄", "Convert to Markdown"))
        self.register(ToolMeta("sandbox_get_browser_info", ToolCategory.NETWORK, "🌐", "Browser Info"))
        self.register(ToolMeta("sandbox_browser_screenshot", ToolCategory.NETWORK, "📸", "Browser Screenshot"))
        self.register(ToolMeta("sandbox_browser_execute_action", ToolCategory.NETWORK, "🖱️", "Browser Action"))

        # ── ToolUniverse 科研工具类 ──
        # self.register(ToolMeta("tooluniverse_search", ToolCategory.DATA, "🔬", "Search Scientific Tools"))
        # self.register(ToolMeta("tooluniverse_info", ToolCategory.DATA, "📋", "Tool Specification"))
        # self.register(ToolMeta("tooluniverse_run", ToolCategory.DATA, "🧪", "Run Scientific Tool"))

        # ── 技能类 ──
        self.register(ToolMeta("skill", ToolCategory.SKILL, "🎯", "Skill"))
        self.register(ToolMeta("propose_skill_save", ToolCategory.SKILL, "💾", "Save Skill"))
        self.register(ToolMeta("propose_tool_save", ToolCategory.CUSTOM, "🔧", "Save Tool"))

        # ── 脚本执行类 ──
        self.register(ToolMeta("run_python_script", ToolCategory.EXECUTION, "🐍", "Run Python"))

    def register(self, tool: ToolMeta):
        self._tools[tool.name] = tool

    def register_sandbox_tool(self, name: str, description: str):
        """注册一个在沙箱中执行的外部代理工具。"""
        self.register(ToolMeta(name, ToolCategory.EXECUTION, "🔧", description))
        self._extra_meta[name] = {"sandbox": True}

    def get(self, name: str) -> Optional[ToolMeta]:
        return self._tools.get(name)

    def get_icon(self, name: str) -> str:
        tool = self.get(name)
        return tool.icon if tool else "🔧"

    def get_category(self, name: str) -> str:
        tool = self.get(name)
        return tool.category.value if tool else ToolCategory.CUSTOM.value

    def get_description(self, name: str) -> str:
        tool = self.get(name)
        return tool.description if tool else name

    def get_meta_dict(self, name: str) -> Dict[str, Any]:
        tool = self.get(name)
        if tool:
            d: Dict[str, Any] = tool.to_dict()
            extra = self._extra_meta.get(name)
            if extra:
                d.update(extra)
            return d
        return {
            "name": name,
            "category": ToolCategory.CUSTOM.value,
            "icon": "🔧",
            "description": name,
        }


# ───────────────────────────────────────────────────────────────────
# SSE 协议管理器（单例）
# ───────────────────────────────────────────────────────────────────

class SSEProtocolManager:
    """SSE 协议管理器 — 提供统一的事件 ID 生成与工具元数据查询"""

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self._event_id_counter = 0

    def generate_event_id(self) -> str:
        self._event_id_counter += 1
        return f"evt_{uuid.uuid4().hex[:8]}_{self._event_id_counter}"

    def now_ts(self) -> int:
        return int(time.time())

    def get_tool_meta(self, tool_function: str) -> Dict[str, str]:
        """根据工具函数名获取元数据"""
        return self.tool_registry.get_meta_dict(tool_function)

    def register_tool(self, name: str, category: ToolCategory, icon: str, description: str):
        """动态注册工具"""
        self.tool_registry.register(ToolMeta(name, category, icon, description))

    def register_sandbox_tool(self, name: str, description: str):
        """注册一个沙箱执行的外部代理工具（tool_meta 会带 sandbox: true）"""
        self.tool_registry.register_sandbox_tool(name, description)


# 全局单例
_protocol_manager: Optional[SSEProtocolManager] = None


def get_protocol_manager() -> SSEProtocolManager:
    """获取全局 SSE 协议管理器实例"""
    global _protocol_manager
    if _protocol_manager is None:
        _protocol_manager = SSEProtocolManager()
    return _protocol_manager
