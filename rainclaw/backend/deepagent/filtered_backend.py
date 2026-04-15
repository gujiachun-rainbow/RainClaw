"""
FilteredFilesystemBackend — 支持屏蔽特定 skills 的文件系统后端。

继承 deepagents 的 FilesystemBackend，对所有文件操作（ls/read/write/edit/glob/grep）
进行屏蔽检查，使被屏蔽的 skill 对 deepagents 完全不可见。
"""
from __future__ import annotations

from typing import Set

from loguru import logger
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.protocol import (
    EditResult,
    FileInfo,
    GrepMatch,
    WriteResult,
)


class FilteredFilesystemBackend(FilesystemBackend):
    """FilesystemBackend with skill-level blocking on ALL operations.

    Any path whose top-level directory name appears in the blocked set
    is rejected: ls hides it, read/write/edit raise errors, glob/grep
    filter it out of results.
    """

    def __init__(self, blocked_skills: Set[str] | None = None, **kwargs):
        super().__init__(**kwargs)
        self._blocked = set(blocked_skills or [])

    def _top_level_name(self, path: str) -> str:
        """Extract the first path component (skill directory name)."""
        return path.strip("/").split("/")[0] if path.strip("/") else ""

    def _path_is_blocked(self, path: str) -> bool:
        name = self._top_level_name(path)
        return name != "" and name in self._blocked

    def _entry_is_blocked(self, entry: FileInfo) -> bool:
        return self._path_is_blocked(entry.get("path", ""))

    # ── ls ────────────────────────────────────────────────────────

    def ls_info(self, path: str) -> list[FileInfo]:
        if self._path_is_blocked(path):
            return []
        entries = super().ls_info(path)
        return [e for e in entries if not self._entry_is_blocked(e)]

    async def als_info(self, path: str) -> list[FileInfo]:
        if self._path_is_blocked(path):
            return []
        entries = await super().als_info(path)
        return [e for e in entries if not self._entry_is_blocked(e)]

    # ── read ──────────────────────────────────────────────────────

    def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        if self._path_is_blocked(file_path):
            raise FileNotFoundError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return super().read(file_path, offset, limit)

    async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> str:
        if self._path_is_blocked(file_path):
            raise FileNotFoundError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return await super().aread(file_path, offset, limit)

    # ── write ─────────────────────────────────────────────────────

    def write(self, file_path: str, content: str) -> WriteResult:
        if self._path_is_blocked(file_path):
            raise PermissionError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return super().write(file_path, content)

    async def awrite(self, file_path: str, content: str) -> WriteResult:
        if self._path_is_blocked(file_path):
            raise PermissionError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return await super().awrite(file_path, content)

    # ── edit ──────────────────────────────────────────────────────

    def edit(self, file_path: str, old_string: str, new_string: str,
             replace_all: bool = False) -> EditResult:
        if self._path_is_blocked(file_path):
            raise PermissionError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return super().edit(file_path, old_string, new_string, replace_all)

    async def aedit(self, file_path: str, old_string: str, new_string: str,
                    replace_all: bool = False) -> EditResult:
        if self._path_is_blocked(file_path):
            raise PermissionError(f"Skill is blocked: {self._top_level_name(file_path)}")
        return await super().aedit(file_path, old_string, new_string, replace_all)

    # ── glob ──────────────────────────────────────────────────────

    def glob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        if self._path_is_blocked(path):
            return []
        entries = super().glob_info(pattern, path)
        return [e for e in entries if not self._entry_is_blocked(e)]

    async def aglob_info(self, pattern: str, path: str = "/") -> list[FileInfo]:
        if self._path_is_blocked(path):
            return []
        entries = await super().aglob_info(pattern, path)
        return [e for e in entries if not self._entry_is_blocked(e)]

    # ── grep ──────────────────────────────────────────────────────

    def grep_raw(self, pattern: str, path: str | None = None,
                 glob: str | None = None) -> list[GrepMatch] | str:
        if path and self._path_is_blocked(path):
            return []
        result = super().grep_raw(pattern, path, glob)
        if isinstance(result, list):
            return [m for m in result if not self._path_is_blocked(m.get("file", ""))]
        return result

    async def agrep_raw(self, pattern: str, path: str | None = None,
                        glob: str | None = None) -> list[GrepMatch] | str:
        if path and self._path_is_blocked(path):
            return []
        result = await super().agrep_raw(pattern, path, glob)
        if isinstance(result, list):
            return [m for m in result if not self._path_is_blocked(m.get("file", ""))]
        return result
