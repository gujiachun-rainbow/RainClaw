from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from api import verify_api_key

from config import DEFAULT_SEARCH_LIMIT, ENGINES
from service.search import CrawlRequest, crawl, make_searxng_request
import logger
from typing import List


router = APIRouter(dependencies=[Depends(verify_api_key)])


class SearchRequest(BaseModel):
    query: str
    limit: int = DEFAULT_SEARCH_LIMIT
    engines: List[str] = ENGINES


async def _perform_search(search_request: SearchRequest) -> dict:
    return await make_searxng_request(
        query=search_request.query,
        limit=search_request.limit,
        engines=search_request.engines,
    )


@router.post("/web_search")
async def web_search(search_request: SearchRequest):
    try:
        logger.info(f"开始搜索: {search_request.query}")

        response = await _perform_search(search_request)

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索过程发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search(search_request: SearchRequest, request: Request):
    try:
        logger.info(f"开始搜索: {search_request.query}")

        response = await _perform_search(search_request)

        results = response.get("results", [])
        if not results:
            logger.warning("未找到搜索结果")
            raise HTTPException(status_code=404, detail="未找到搜索结果")

        urls = [
            result["url"]
            for result in results[: search_request.limit]
            if "url" in result
        ]
        if not urls:
            logger.warning("未找到有效的URL")
            raise HTTPException(status_code=404, detail="未找到有效的URL")

        logger.info(f"找到 {len(urls)} 个URL，开始爬取")

        crawl_result = await crawl(
            request.app.state.crawler,
            CrawlRequest(
                results=results[: search_request.limit],
                instruction=search_request.query,
            ),
        )
        crawl_result["query"] = search_request.query
        return crawl_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索过程发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
