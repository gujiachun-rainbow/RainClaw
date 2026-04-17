import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from loguru import logger

from backend.user.dependencies import require_user, User

router = APIRouter(prefix="/file", tags=["file"])

_ALLOWED_PREFIXES = [
    Path(p).resolve()
    for p in os.environ.get(
        "FILE_DOWNLOAD_ALLOWED_PREFIXES", "/tmp,/app,/home/rainclaw"
    ).split(",")
    if p.strip()
]


@router.get("/download")
async def download_file(
    path: str = Query(..., min_length=1),
    _current_user: User = Depends(require_user),
):
    """Download file from local filesystem (restricted to allowed prefixes)."""
    logger.info(f"File download requested for path: {path}")
    try:
        target_path = Path(path).resolve()

        is_allowed = any(
            target_path == prefix or prefix in target_path.parents
            for prefix in _ALLOWED_PREFIXES
        )
        if not is_allowed:
            logger.warning(f"Access denied for path: {path} (Resolved: {target_path})")
            raise HTTPException(status_code=403, detail="Access denied: Path not allowed")

        if not target_path.exists() or not target_path.is_file():
            logger.warning(f"File not found: {path} (Resolved: {target_path})")
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            path=str(target_path),
            filename=target_path.name,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("download_file failed")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
