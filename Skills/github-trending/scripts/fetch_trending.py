#!/usr/bin/env python3
"""
获取 GitHub 最新热门开源项目
通过 GitHub Search API 按照星标数量排序获取最近创建或更新的热门项目。
"""

import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta


def fetch_trending(since="daily", language="", spoken_language=""):
    """
    获取 GitHub 热门项目

    Args:
        since: 时间范围 - daily(每日), weekly(每周), monthly(每月)
        language: 编程语言筛选 (如 python, javascript, 留空为全部)
        spoken_language: 自然语言筛选 (暂未使用, 保留兼容)
    """
    # 根据时间范围计算日期
    now = datetime.utcnow()
    if since == "weekly":
        date_threshold = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    elif since == "monthly":
        date_threshold = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    else:  # daily
        date_threshold = (now - timedelta(days=1)).strftime("%Y-%m-%d")

    # 构建 GitHub Search API URL
    # 按 stars 排序，筛选在指定日期之后推送过的仓库
    query_parts = [f"pushed:>{date_threshold}"]
    if language:
        query_parts.append(f"language:{language}")

    query = " ".join(query_parts)
    url = (
        f"https://api.github.com/search/repositories"
        f"?q={urllib.request.quote(query)}"
        f"&sort=stars&order=desc&per_page=25"
    )

    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Trending-Skill"
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"GitHub API 请求失败: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"网络错误: {e.reason}", file=sys.stderr)
        sys.exit(1)

    items = data.get("items", [])
    if not items:
        print("未找到热门项目，请稍后重试。")
        return

    # 输出为 JSON 格式
    results = []
    for repo in items:
        results.append({
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description") or "暂无描述",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language") or "未知",
            "forks": repo.get("forks_count", 0),
            "today_stars": repo.get("stargazers_count", 0),  # API 不直接提供日增 star
        })

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    since = sys.argv[1] if len(sys.argv) > 1 else "daily"
    language = sys.argv[2] if len(sys.argv) > 2 else ""
    fetch_trending(since, language)
