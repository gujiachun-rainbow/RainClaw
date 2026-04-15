# 学术来源检索指南

本文档提供 arXiv、PubMed、Semantic Scholar、Google Scholar 等学术数据库的检索方法，供 Phase 4 学术路径使用。

---

## 1. arXiv 检索

arXiv 覆盖物理、数学、计算机科学、统计学、电子工程、生物学(q-bio)、金融(q-fin) 等领域。

### 方法 A：通过 web_search 间接检索（推荐首选）

最简单可靠的方式，利用搜索引擎的索引：

```
web_search("site:arxiv.org {关键词} {年份}")
```

示例：
```
web_search("site:arxiv.org large language model drug discovery 2025 2026")
web_search("site:arxiv.org transformer protein structure prediction")
```

从搜索结果中获取论文的 arXiv ID 和 URL，然后用 `web_crawl` 抓取论文摘要页获取详细信息：

```
web_crawl("https://arxiv.org/abs/2401.12345")
```

### 方法 B：通过 arXiv API 批量检索

当需要获取大量候选论文时，使用 arXiv API。通过 `web_crawl` 访问 API URL：

```
web_crawl("https://export.arxiv.org/api/query?search_query=all:{keywords}&max_results=20&sortBy=submittedDate&sortOrder=descending")
```

**query 构造规则**：
- `all:{keywords}` — 搜索所有字段（标题、摘要、全文）
- `ti:{keywords}` — 仅搜索标题
- `abs:{keywords}` — 仅搜索摘要
- `au:{author_name}` — 搜索作者
- `cat:{category}` — 搜索分类（如 `cs.AI`, `cs.CL`, `q-bio.BM`）
- 用 `+AND+` 连接多个条件，用 `+OR+` 表示或关系
- 用 `%22` 表示引号（精确匹配短语）

**示例 URL**：
```
https://export.arxiv.org/api/query?search_query=all:large+language+model+AND+all:drug+discovery&max_results=20&sortBy=submittedDate&sortOrder=descending
```

API 返回 Atom XML 格式。从中提取每篇论文的：
- `<title>` — 标题
- `<summary>` — 摘要
- `<author><name>` — 作者列表
- `<published>` — 发布日期
- `<link href="..." title="pdf"/>` — PDF 下载链接
- `<arxiv:primary_category>` — 主要分类

### arXiv 常用分类

| 代码 | 领域 |
|------|------|
| cs.AI | 人工智能 |
| cs.CL | 计算语言学/NLP |
| cs.CV | 计算机视觉 |
| cs.LG | 机器学习 |
| cs.CR | 密码学与安全 |
| cs.SE | 软件工程 |
| stat.ML | 统计机器学习 |
| q-bio.BM | 生物分子 |
| q-bio.GN | 基因组学 |
| physics.comp-ph | 计算物理 |
| cond-mat | 凝聚态物理 |
| quant-ph | 量子物理 |

### 下载与解析 PDF

```bash
# 下载 PDF
wget -q "https://arxiv.org/pdf/2401.12345v1.pdf" -O research_data/papers/2401.12345.pdf

# 提取文本（学术论文首选 pdftotext -layout）
pdftotext -layout research_data/papers/2401.12345.pdf research_data/papers/2401.12345.txt
```

提取后重点阅读以下部分：
- **Abstract** — 一句话核心贡献
- **Introduction** — 研究动机和问题定义
- **Method / Approach** — 技术路线（可跳过公式细节，关注整体思路）
- **Experiments / Results** — 关键数据和对比结果
- **Conclusion** — 总结和局限性

---

## 2. PubMed 检索

PubMed 覆盖生物医学和生命科学领域，是医学/生物类调研的核心数据库。

### 通过 web_search 检索

```
web_search("site:pubmed.ncbi.nlm.nih.gov {关键词}")
```

### 通过 PubMed API (E-utilities)

搜索并获取论文列表：

```
web_crawl("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=20&sort=date")
```

获取论文详细摘要（用逗号分隔多个 PMID）：

```
web_crawl("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid1},{pmid2}&retmode=xml")
```

**注意**：PubMed 论文大多数不开放获取。如果需要全文：
- 检查论文是否在 PubMed Central (PMC) 有免费全文
- `web_crawl("https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{id}/")` 获取 PMC 全文
- 或通过 DOI 检查出版商网站是否提供开放获取

---

## 3. Semantic Scholar 检索

Semantic Scholar 跨领域覆盖，并提供引用关系和语义相关性。

### 通过 web_search

```
web_search("site:semanticscholar.org {关键词}")
```

### 通过 API

```
web_crawl("https://api.semanticscholar.org/graph/v1/paper/search?query={keywords}&limit=20&fields=title,abstract,authors,year,citationCount,url,openAccessPdf")
```

返回 JSON 格式。`openAccessPdf` 字段包含可下载的 PDF URL（如果有）。

Semantic Scholar 的优势：
- 提供引用计数，可用于判断论文影响力
- 跨多个数据库（arXiv、PubMed、ACM 等）
- `openAccessPdf` 字段直接给出可下载的 PDF

---

## 4. Google Scholar 间接检索

Google Scholar 不提供官方 API，且可能拦截爬虫。通过 `web_search` 间接使用：

```
web_search("{关键词} site:scholar.google.com")
web_search("{关键词} filetype:pdf")
```

主要用途：
- 补充 arXiv/PubMed 覆盖不到的领域（社会科学、人文、工程等）
- 通过 "Cited by" 追溯引用关系
- 查找特定论文的开放获取版本

---

## 5. 论文筛选策略

从检索结果中筛选 5-10 篇最相关的论文，依据：

1. **相关性**（最重要）：论文主题与子课题问题的匹配度
2. **时效性**：优先最近 1-2 年的论文，除非是经典开创性工作
3. **影响力**：引用次数、发表在知名会议/期刊
4. **信息密度**：survey/review 论文通常比单篇实验论文信息密度更高，适合做背景综述
5. **互补性**：选择覆盖不同角度/方法的论文，避免重复

**当第一轮结果不理想时的调整策略**：
- 用已找到论文摘要中的术语替换原始关键词
- 从高引论文的参考文献列表中追溯关键引用
- 搜索 "survey" 或 "review" 类论文
- 放宽时间范围或换分类搜索

---

## 6. 引用格式

为参考文献列表记录以下信息：

```json
[
  "Author1, Author2, et al. Paper Title. Conference/Journal, Year. https://arxiv.org/abs/xxxx.xxxxx",
  "Author1, Author2. Paper Title. PubMed PMID: 12345678, Year. https://pubmed.ncbi.nlm.nih.gov/12345678/"
]
```
