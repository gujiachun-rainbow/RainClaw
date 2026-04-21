from typing import Dict, Any
from codecs import encode
import json

import aiohttp
from pydantic import BaseModel

from config import (
    SEARXNG_HOST,
    SEARXNG_PORT,
    SEARXNG_BASE_PATH,
    ENGINES
)
from service.crawler import WebCrawler
import logger


class CrawlRequest(BaseModel):
    results: list[dict]
    instruction: str


async def crawl(crawler: WebCrawler, request: CrawlRequest):
    return await crawler.crawl_earch_results(request.results, request.instruction)


async def make_searxng_request(
    query: str,
    limit: int = 10,
    engines: list[str] = ENGINES,
) -> Dict[str, Any]:
    """向SearXNG发送搜索请求

    Args:
        query: 搜索查询字符串   
        limit: 返回结果数量限制
        engines: 启用的搜索引擎列表

    Returns:
        dict: SearXNG返回的搜索结果

    Raises:
        Exception: 当请求失败时抛出异常
    """
    if not engines:
        engines = ENGINES
    try:
        dataList = []
        boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'

        form_data = {
            'q': query,
            'format': 'json',
            'language': 'auto',
            # 'time_range': 'week',
            'safesearch': '0',
            'pageno': '1',
            'category_general': '1'
        }

        for key, value in form_data.items():
            dataList.append(encode('--' + boundary))
            dataList.append(encode(f'Content-Disposition: form-data; name={key};'))
            dataList.append(encode('Content-Type: {}'.format('text/plain')))
            dataList.append(encode(''))
            dataList.append(encode(str(value)))

        dataList.append(encode('--' + boundary + '--'))
        dataList.append(encode(''))
        body = b'\r\n'.join(dataList)
        cookie = ["method=POST", "categories=general"]
        cookie_engines = "\054".join([engine for engine in ENGINES if engine not in engines])
        if cookie_engines:
            cookie.append(f"disabled_engines={cookie_engines}")
        headers = {
            'Cookie': "; ".join(cookie),
            'User-Agent': 'Sear-Crawl4AI/1.0.0',
            'Accept': '*/*',
            'Host': f'{SEARXNG_HOST}:{SEARXNG_PORT}',
            'Connection': 'keep-alive',
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'X-Real-IP': '192.168.10.97'
        }

        url = f"http://{SEARXNG_HOST}:{SEARXNG_PORT}{SEARXNG_BASE_PATH}"
        logger.info(f"SearXNG请求URL: {url}")
        logger.info(f"SearXNG请求Headers: {json.dumps(headers, ensure_ascii=False)}")
        logger.info(f"SearXNG请求Body: {body.decode('utf-8', errors='ignore')}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=body) as response:
                status = response.status
                text = await response.text()
                logger.info(f"SearXNG响应状态码: {status}")
                logger.info(f"SearXNG响应Body: {text}")
                return await response.json()
    except Exception as e:
        logger.error(f"SearXNG请求失败: {str(e)}")
        raise Exception(f"搜索请求失败: {str(e)}")
