from fastapi import HTTPException, Request
import os
import logger


async def verify_api_key(request: Request):
    """验证 API Key。如果未设置 API_KEY 环境变量，则跳过验证（内部调用）。"""
    api_key = os.environ.get("API_KEY")
    if not api_key:
        # API_KEY 未设置，跳过验证（适用于 Docker 内部服务间调用）
        return

    header_api_key = request.headers.get("apikey")
    if not header_api_key or header_api_key != api_key:
        logger.error("API_KEY 验证失败")
        raise HTTPException(
            status_code=403,
            detail="apikey 验证失败, 请检查请求头中的 apikey 是否正确",
        )
