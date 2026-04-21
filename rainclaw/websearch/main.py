# -*- coding: utf-8 -*-
"""
Sear-Crawl4AI - 一个基于SearXNG和Crawl4AI的开源搜索和爬取工具

Sear-Crawl4AI is an open-source alternative to Tavily, providing search and crawling
capabilities using SearXNG as the search engine and Crawl4AI for web crawling.

此项目可以作为Tavily的开源替代品，提供类似的搜索和网页内容提取功能。
"""

from fastapi import FastAPI
import sys
import subprocess
from config import API_HOST, API_PORT
from service.crawler import WebCrawler
from api.search import router as search_router
from api.crawler import router as crawler_router
import logger

app = FastAPI(
    title="Sear-Crawl4AI API",
    description="一个基于SearXNG和Crawl4AI的开源搜索和爬取工具，可作为Tavily的开源替代品",
    version="1.0.0"
)

app.include_router(search_router)
app.include_router(crawler_router)


@app.on_event("startup")
async def startup_event():
    """
    应用程序启动事件处理函数

    在FastAPI应用启动时执行，负责初始化爬虫和安装必要的浏览器
    """
    # 配置日志级别
    logger.setup_logger("INFO")
    logger.info("Sear-Crawl4AI 服务启动中...")

    # 检查并安装浏览器
    logger.info("检查 Playwright 浏览器...")
    try:
        # 尝试安装浏览器
        subprocess.run([sys.executable, "-m", "playwright",
                       "install", "chromium"], check=True)
        logger.info("Playwright 浏览器安装成功或已存在")
    except subprocess.CalledProcessError as e:
        logger.error(f"浏览器安装失败: {e}")
        raise

    # 初始化爬虫
    app.state.crawler = WebCrawler()
    await app.state.crawler.initialize()
    logger.info("爬虫初始化完成")

    # 输出配置信息
    logger.info(f"API服务运行在: http://{API_HOST}:{API_PORT}")
    logger.info("Sear-Crawl4AI 服务启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """
    应用程序关闭事件处理函数

    在FastAPI应用关闭时执行，负责释放爬虫资源
    """
    crawler = getattr(app.state, "crawler", None)
    if crawler:
        await crawler.close()
        logger.info("爬虫资源已释放")
    logger.info("Sear-Crawl4AI 服务已关闭")
if __name__ == "__main__":
    # 程序入口点
    logger.info("通过命令行启动Sear-Crawl4AI服务")
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
