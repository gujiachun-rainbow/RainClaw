# -*- coding: utf-8 -*-
"""
爬虫模块 - 提供网页爬取和内容处理功能

This module provides web crawling and content processing functionality.
It encapsulates the AsyncWebCrawler from crawl4ai library and provides
high-level methods for crawling web pages and processing their content.
"""

from typing import List, Dict, Any
from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter
import markdown
from bs4 import BeautifulSoup
import re
from fastapi import HTTPException

# 导入配置和日志模块
from config import CONTENT_FILTER_THRESHOLD, WORD_COUNT_THRESHOLD
import logger


class WebCrawler:
    """网页爬虫类，封装了网页爬取和内容处理的功能"""

    def __init__(self):
        """初始化爬虫实例"""
        self.crawler = None
        logger.info("初始化WebCrawler实例")

    async def initialize(self) -> None:
        """初始化AsyncWebCrawler实例

        必须在使用爬虫前调用此方法
        """
        # 配置浏览器
        browser_config = BrowserConfig(headless=True, verbose=True)
        # 初始化爬虫
        self.crawler = await AsyncWebCrawler(config=browser_config).__aenter__()
        logger.info("AsyncWebCrawler初始化完成")

    async def close(self) -> None:
        """关闭爬虫实例，释放资源"""
        if self.crawler:
            await self.crawler.__aexit__(None, None, None)
            logger.info("AsyncWebCrawler已关闭")

    @staticmethod
    def markdown_to_text_regex(markdown_str: str) -> str:
        """使用正则表达式将Markdown文本转换为纯文本

        Args:
            markdown_str: Markdown格式的文本

        Returns:
            str: 转换后的纯文本
        """
        # 移除标题符号
        text = re.sub(r'#+\s*', '', markdown_str)

        # 移除链接和图片
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)

        # 移除粗体、斜体等强调符号
        text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
        text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)

        # 移除列表符号
        text = re.sub(r'^[\*\-\+]\s*', '', text, flags=re.MULTILINE)

        # 移除代码块
        text = re.sub(r'`{3}.*?`{3}', '', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'\1', text)

        # 移除引用块
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        return text.strip()

    @staticmethod
    def markdown_to_text(markdown_str: str) -> str:
        """使用markdown和BeautifulSoup库将Markdown文本转换为纯文本

        Args:
            markdown_str: Markdown格式的文本

        Returns:
            str: 转换后的纯文本
        """
        html = markdown.markdown(markdown_str, extensions=['fenced_code'])
        # 用 BeautifulSoup 提取纯文本
        soup = BeautifulSoup(html, "html.parser")

        text = soup.get_text(separator="\n")  # 保留段落换行

        # 清理多余空行
        cleaned_text = "\n".join([line.strip()
                             for line in text.split("\n") if line.strip()])

        return cleaned_text

    async def crawl_urls(self, urls: List[str]) -> Dict[str, Any]:
        if not self.crawler:
            logger.warning("爬虫未初始化，正在自动初始化")
            await self.initialize()

        # 配置Markdown生成器
        md_generator = DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=CONTENT_FILTER_THRESHOLD),
            options={
                "ignore_links": True,
                "ignore_images": True,
                "escape_html": False,
            }
        )
        # 配置爬虫运行参数
        run_config = CrawlerRunConfig(
            word_count_threshold=WORD_COUNT_THRESHOLD,
            exclude_external_links=True,    # 移除外部链接
            remove_overlay_elements=True,   # 移除弹窗/模态框
            excluded_tags=['img', 'header', 'footer', 'iframe', 'nav'],      # 排除图片标签
            process_iframes=True,           # 处理iframe
            markdown_generator=md_generator,
            cache_mode=CacheMode.BYPASS     # 不使用缓存
        )
 
        logger.info(f"开始爬取URLs: {', '.join(urls)}")
        
        # 创建一个列表来存储所有成功URL的爬取结果
        all_results = {}
        retry_urls = [url for url in urls]
        retry_times = 2
        for _i in range(retry_times):
            if not retry_urls:
                break
            results = await self.crawler.arun_many(urls=retry_urls, config=run_config)
            # 第一次爬取处理
            for i, result in enumerate(results):
                try:
                    if result is None:
                        logger.debug(f"URL爬取结果为None: {result.url}")
                        continue

                    if not hasattr(result, 'success'):
                        logger.debug(f"URL爬取结果缺少success属性: {result.url}")
                        continue

                    if result.success:
                        if not hasattr(result, 'markdown') or not hasattr(result.markdown, 'fit_markdown'):
                            logger.debug(f"URL爬取结果缺少markdown内容: {result.url}")
                            continue
                        # 将成功的结果的markdown内容添加到列表中
                        result_with_source = result.markdown.fit_markdown + '\n\n'
                        result_with_source = self.markdown_to_text_regex(self.markdown_to_text(result_with_source))
                        all_results[result.url] = result_with_source
                        logger.info(f"成功爬取URL: {result.url}")
                        retry_urls.remove(result.url)
                    else:
                        logger.debug(f"URL爬取失败: {result.url}")
                except Exception as e:
                    # 记录需要重试的URL
                    error_msg = str(e)
                    logger.warning(f"URL第一次爬取失败: {result.url}, 错误信息: {error_msg}")
        # all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        return {
            "results": all_results,
            "failed_urls": retry_urls
        }


    async def crawl_earch_results(self, url_search_results: List[dict], instruction: str) -> Dict[str, Any]:
        """爬取多个URL并处理内容

        Args:
            results: 要爬取的URL列表
            instruction: 爬取指令，通常是搜索查询

        Returns:
            Dict[str, Any]: 包含处理后内容、成功数量和失败URL的字典

        Raises:
            HTTPException: 当所有URL爬取均失败时抛出异常
        """
        urls: List[str] = []
        url2search_results: Dict[str, dict] = {}
        for url_search_result in url_search_results:
            url = url_search_result.get("url")
            if url:
                urls.append(url)
                url2search_results[url] = url_search_result
        final_search_crawl_results: List[dict] = []
        failed_urls: List[str] = []
        try:
            crawl_results = await self.crawl_urls(urls)
            url_crawl_results = crawl_results["results"]
            failed_urls = crawl_results["failed_urls"]
            for url, url_crawl_result in url_crawl_results.items():
                url_search_result = url2search_results.get(url)
                if url_search_result:
                    url_search_result["content"] = url_crawl_result
                    final_search_crawl_results.append(url_search_result)
            if not url_crawl_results:
                logger.error("所有URL爬取均失败")
                raise HTTPException(status_code=500, detail="所有URL爬取均失败")
            if final_search_crawl_results:
                final_search_crawl_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            response = {
                "success_count": len(final_search_crawl_results),
                "failed_urls": failed_urls,
                "results": final_search_crawl_results,
            }
            logger.info(
                f"爬取完成，成功: {len(final_search_crawl_results)}，失败: {len(failed_urls)}"
            )
            return response
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"爬取过程发生异常: {str(e)}")
            if not failed_urls:
                failed_urls = urls
            response = {
                "success_count": len(final_search_crawl_results),
                "failed_urls": failed_urls,
                "results": [],
            }
            logger.info(
                f"爬取完成，成功: {len(final_search_crawl_results)}，失败: {len(failed_urls)}"
            )
            return response
