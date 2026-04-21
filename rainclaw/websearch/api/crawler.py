from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List

from api import verify_api_key
from service.crawler import WebCrawler
import logger


router = APIRouter(dependencies=[Depends(verify_api_key)])


class CrawlUrlsRequest(BaseModel):
    urls: List[str]


@router.post("/crawl_urls")
async def crawl_urls(request_body: CrawlUrlsRequest, request: Request):
    crawler = getattr(request.app.state, "crawler", None)
    if crawler is None or not isinstance(crawler, WebCrawler):
        logger.error("爬虫实例未初始化")
        raise HTTPException(status_code=500, detail="爬虫实例未初始化")

    try:
        logger.info(f"开始爬取 URLs: {', '.join(request_body.urls)}")
        result = await crawler.crawl_urls(request_body.urls)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"爬取过程发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
