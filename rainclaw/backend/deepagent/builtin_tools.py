import asyncio
import logging

logger = logging.getLogger(__name__)

def _doc_to_entry(doc: dict) -> dict:
    """MongoDB 文档转前端友好格式。"""
    return {
        "name": doc.get("name", ""),
        "host": doc.get("host", ""),
        "username": doc.get("username", ""),
        "password": doc.get("password", ""),
        "port": doc.get("port", ""),
        "database": doc.get("database_name", ""),
        "db_type": doc.get("db_type", ""),
    }

async def get_datasource_by_code(code: str) -> dict:
    """这个工具是用来获取数据源信息的，根据场景编码code获取数据源信息。

    Args:
        code: 场景编码code

    Returns:
        数据源信息
    """
    logger.info(f"[获取数据源] 开始获取数据源信息: {code}")
    try:
        from backend.mongodb.db import db
        doc = await db.get_collection("datasources").find_one({"code": code})
        logger.info(f"[获取数据源] 内容: {doc}")
        if doc is None:
            return {"error": "数据源不存在"}
        return _doc_to_entry(doc)
    except Exception as exc:
        logger.error(f"[获取数据源] 获取数据源信息失败: {exc}")
        return {"error": str(exc)}
