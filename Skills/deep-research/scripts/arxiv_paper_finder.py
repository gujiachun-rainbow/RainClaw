#!/usr/bin/env python3
"""
arXiv Paper Finder — 从 arXiv 搜索、筛选、下载论文

工作流程:
  1. 接收用户问题 + 拆解后的多个 query
  2. 用每个 query 查询 arXiv API，合计获取 ~50 篇论文
  3. 去重，按相关性评分排序
  4. 筛选 top 12-15 篇
  5. 下载 PDF 到 workspace

用法:
    python3 arxiv_paper_finder.py <config.json>

config.json 格式:
{
  "question": "用户原始问题",
  "queries": [
    {"arxiv_query": "abs:data+center+AND+abs:cooling", "label": "数据中心冷却"},
    ...
  ],
  "target_total": 50,
  "top_k": 15,
  "output_dir": "research_papers",
  "relevance_phrases": ["data center", "cooling", "thermal management"]
}

queries 也支持简单字符串列表（自动转换为 abs: 搜索）。
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
import re
from pathlib import Path

ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def build_arxiv_query(query_item):
    """
    将 query 配置项转换为 arXiv API 的 search_query 参数。
    支持两种格式:
      - 字符串: "data center cooling" → 自动构造 arXiv 查询
      - 字典: {"arxiv_query": "...", "label": "..."} → 直接使用 arxiv_query
    arXiv API 中短语用 %22 (URL编码引号) 包裹，词间用 + 连接。
    """
    if isinstance(query_item, dict):
        return query_item["arxiv_query"], query_item.get("label", "")

    words = query_item.strip().split()
    phrase = "+".join(words)
    return f"abs:{phrase}", query_item


def search_arxiv(query_str, max_results=10):
    """通过 arXiv API 搜索论文，query_str 已是格式化好的搜索表达式"""
    qs = (
        f"search_query={query_str}"
        f"&max_results={max_results}"
        f"&sortBy=relevance"
        f"&sortOrder=descending"
    )
    url = f"{ARXIV_API}?{qs}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DeepResearch/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  [ERROR] 搜索失败: {e}")
        return []

    root = ET.fromstring(xml_data)
    papers = []

    for entry in root.findall(f"{ATOM_NS}entry"):
        id_elem = entry.find(f"{ATOM_NS}id")
        title_elem = entry.find(f"{ATOM_NS}title")
        summary_elem = entry.find(f"{ATOM_NS}summary")
        published_elem = entry.find(f"{ATOM_NS}published")

        if id_elem is None or title_elem is None or summary_elem is None:
            continue

        raw_id = id_elem.text.strip()
        paper_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id
        paper_id = re.sub(r"v\d+$", "", paper_id)

        title = " ".join(title_elem.text.strip().split())
        abstract = " ".join(summary_elem.text.strip().split())
        published = published_elem.text[:10] if published_elem is not None else ""

        authors = []
        for author in entry.findall(f"{ATOM_NS}author"):
            name_elem = author.find(f"{ATOM_NS}name")
            if name_elem is not None:
                authors.append(name_elem.text.strip())

        pdf_url = None
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.get("title") == "pdf":
                pdf_url = link.get("href")
                break
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{paper_id}"

        categories = []
        prim_cat = entry.find(f"{ARXIV_NS}primary_category")
        if prim_cat is not None:
            categories.append(prim_cat.get("term", ""))
        for cat in entry.findall(f"{ATOM_NS}category"):
            t = cat.get("term", "")
            if t and t not in categories:
                categories.append(t)

        papers.append({
            "id": paper_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published,
            "pdf_url": pdf_url,
            "categories": categories,
        })

    return papers


def deduplicate(papers):
    """按 arXiv ID 去重，记录被多个 query 命中的情况"""
    seen = {}
    for p in papers:
        pid = p["id"]
        if pid not in seen:
            p["hit_count"] = 1
            seen[pid] = p
        else:
            seen[pid]["hit_count"] = seen[pid].get("hit_count", 1) + 1
    return list(seen.values())


def score_paper(paper, phrases):
    """
    多维度相关性评分:
      - 标题命中短语: +5/phrase
      - 摘要命中短语: +2/phrase
      - 多 query 命中: +3/extra hit
      - 近期加分: 2025+ → +3, 2024 → +2, 2023 → +1
    """
    score = 0
    title_lower = paper["title"].lower()
    abstract_lower = paper["abstract"].lower()

    for phrase in phrases:
        pl = phrase.lower()
        if pl in title_lower:
            score += 5
        if pl in abstract_lower:
            score += 2

    extra_hits = paper.get("hit_count", 1) - 1
    score += extra_hits * 3

    year = int(paper["published"][:4]) if len(paper.get("published", "")) >= 4 else 0
    if year >= 2025:
        score += 3
    elif year >= 2024:
        score += 2
    elif year >= 2023:
        score += 1

    return score


def download_pdf(paper, output_dir):
    """下载单篇论文 PDF"""
    pdf_url = paper["pdf_url"]
    if not pdf_url.endswith(".pdf"):
        pdf_url += ".pdf"

    safe_id = paper["id"].replace("/", "_")
    filename = f"{safe_id}.pdf"
    filepath = os.path.join(output_dir, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  [SKIP] 已存在: {filename} ({size_kb:.0f} KB)")
        return filepath

    try:
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "DeepResearch/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(filepath, "wb") as f:
            f.write(data)
        size_kb = len(data) / 1024
        print(f"  [OK] {filename} ({size_kb:.0f} KB)")
        return filepath
    except Exception as e:
        print(f"  [ERROR] 下载失败 ({filename}): {e}")
        return None


def run(config):
    """执行完整搜索 → 筛选 → 下载流程"""
    question = config["question"]
    queries = config["queries"]
    target_total = config.get("target_total", 50)
    top_k = config.get("top_k", 15)
    output_dir = config.get("output_dir", "research_papers")
    relevance_phrases = config.get("relevance_phrases", [])
    min_score = config.get("min_score", 4)

    os.makedirs(output_dir, exist_ok=True)

    # ── Step 1: 多 query 搜索 ──
    print(f"\n{'=' * 60}")
    print(f"  原始问题: {question}")
    print(f"  查询数量: {len(queries)}")
    print(f"  目标论文: ~{target_total} 篇候选 → TOP {top_k} 篇下载")
    print(f"{'=' * 60}\n")

    per_query = max(5, (target_total // len(queries)) + 3)
    all_papers = []

    for i, q in enumerate(queries):
        arxiv_q, label = build_arxiv_query(q)
        print(f"[{i + 1}/{len(queries)}] \"{label}\"")
        print(f"         query: {arxiv_q[:80]}{'...' if len(arxiv_q) > 80 else ''}")
        papers = search_arxiv(arxiv_q, max_results=per_query)
        print(f"         → 返回 {len(papers)} 篇")
        all_papers.extend(papers)
        if i < len(queries) - 1:
            time.sleep(3)

    # ── Step 2: 去重 ──
    unique = deduplicate(all_papers)
    print(f"\n去重: {len(all_papers)} → {len(unique)} 篇唯一论文\n")

    # ── Step 3: 评分排序 ──
    for p in unique:
        p["relevance_score"] = score_paper(p, relevance_phrases)

    unique.sort(key=lambda p: p["relevance_score"], reverse=True)

    # 保存全部候选
    candidates_path = os.path.join(output_dir, "all_candidates.json")
    with open(candidates_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)
    print(f"全部候选已保存: {candidates_path} ({len(unique)} 篇)\n")

    # 输出全部评分概览
    print(f"--- 全部候选评分概览 ---")
    for i, p in enumerate(unique):
        marker = " ★" if i < top_k and p["relevance_score"] >= min_score else ""
        print(f"  [{i+1:2d}] score={p['relevance_score']:2d}  {p['published']}  {p['title'][:70]}{marker}")
    print()

    # ── Step 4: 筛选 TOP-K ──
    selected = [p for p in unique if p["relevance_score"] >= min_score][:top_k]

    print(f"{'=' * 60}")
    print(f"  筛选结果: {len(selected)} 篇 (score >= {min_score})")
    print(f"{'=' * 60}\n")

    for i, p in enumerate(selected):
        print(f"  [{i + 1}] score={p['relevance_score']}  {p['published']}")
        print(f"      {p['title']}")
        print(f"      ID: {p['id']}")
        auth_str = ", ".join(p["authors"][:3])
        if len(p["authors"]) > 3:
            auth_str += " et al."
        print(f"      Authors: {auth_str}")
        print(f"      Abstract: {p['abstract'][:200]}...")
        print()

    selected_path = os.path.join(output_dir, "selected_papers.json")
    with open(selected_path, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    print(f"筛选结果已保存: {selected_path}\n")

    # ── Step 5: 下载 PDF ──
    print(f"{'=' * 60}")
    print(f"  开始下载 PDF ...")
    print(f"{'=' * 60}\n")

    downloaded = []
    for p in selected:
        fpath = download_pdf(p, output_dir)
        if fpath:
            downloaded.append({"id": p["id"], "title": p["title"], "path": fpath})
        time.sleep(2)

    print(f"\n下载完成: {len(downloaded)}/{len(selected)} 篇\n")

    # ── 保存搜索摘要 ──
    summary = {
        "question": question,
        "queries_used": [
            q if isinstance(q, str) else q.get("label", q.get("arxiv_query", ""))
            for q in queries
        ],
        "total_candidates": len(unique),
        "selected_count": len(selected),
        "downloaded_count": len(downloaded),
        "selected_papers": [
            {
                "id": p["id"],
                "title": p["title"],
                "authors": p["authors"],
                "published": p["published"],
                "abstract": p["abstract"],
                "relevance_score": p["relevance_score"],
                "pdf_url": p["pdf_url"],
            }
            for p in selected
        ],
        "downloaded": downloaded,
    }

    summary_path = os.path.join(output_dir, "search_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"搜索摘要已保存: {summary_path}")

    return summary


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 arxiv_paper_finder.py <config.json>")
        print()
        print("config.json 示例:")
        example = {
            "question": "用户原始问题",
            "queries": [
                {"arxiv_query": 'abs:"data center"+AND+abs:cooling', "label": "数据中心冷却"},
                "liquid cooling immersion data center",
            ],
            "target_total": 50,
            "top_k": 15,
            "output_dir": "research_papers",
            "relevance_phrases": ["data center", "cooling", "thermal"],
            "min_score": 4,
        }
        print(json.dumps(example, ensure_ascii=False, indent=2))
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        cfg = json.load(f)

    run(cfg)
