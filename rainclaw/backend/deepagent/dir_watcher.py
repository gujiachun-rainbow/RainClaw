"""
目录变更监控器 — 通过文件列表 + mtime 快照检测 Tools/ 和 Skills/ 目录变更。

使用方式：
    from backend.deepagent.dir_watcher import watcher
    if watcher.has_changed("/app/Tools"):
        # 重新扫描加载工具
"""

import threading
from pathlib import Path
from typing import Dict, Tuple, FrozenSet

from loguru import logger

_Snapshot = Tuple[FrozenSet[str], float]


class DirWatcher:
    """轻量级目录变更检测（基于 文件列表 + max mtime 对比）。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshots: Dict[str, _Snapshot] = {}

    @staticmethod
    def _take_snapshot(dir_path: str) -> _Snapshot:
        p = Path(dir_path)
        if not p.is_dir():
            return frozenset(), 0.0
        files: set[str] = set()
        max_mtime = 0.0
        for f in p.rglob("*"):
            if f.is_file() and not f.name.startswith("."):
                try:
                    mt = f.stat().st_mtime
                except OSError:
                    mt = 0.0
                files.add(str(f.relative_to(p)))
                max_mtime = max(max_mtime, mt)
        return frozenset(files), max_mtime

    def has_changed(self, dir_path: str) -> bool:
        """检测目录内容是否相比上次调用发生了变更。

        首次调用初始化快照并返回 False。
        """
        with self._lock:
            current = self._take_snapshot(dir_path)
            prev = self._snapshots.get(dir_path)
            self._snapshots[dir_path] = current
            if prev is None:
                logger.info(f"[DirWatcher] 初始化快照: {dir_path} ({len(current[0])} 个文件)")
                return False
            changed = current != prev
            if changed:
                old_files, _ = prev
                new_files, _ = current
                added = new_files - old_files
                removed = old_files - new_files
                parts = []
                if added:
                    parts.append(f"新增={list(added)}")
                if removed:
                    parts.append(f"移除={list(removed)}")
                if not added and not removed:
                    parts.append("文件内容已修改")
                logger.info(f"[DirWatcher] 检测到变更: {dir_path} — {', '.join(parts)}")
            return changed


watcher = DirWatcher()
