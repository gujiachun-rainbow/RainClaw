# 非学术数据源指南

本文档提供行业报告、统计数据、技术文档等非学术信息源的检索策略，供 Phase 4 Web 路径使用。

---

## 1. 信息源分类与优先级

| 优先级 | 信息源类型 | 可信度 | 示例 |
|-------|-----------|--------|------|
| P0 | 政府/国际组织官方数据 | 极高 | 国家统计局、世界银行、WHO、OECD |
| P0 | 行业权威机构报告 | 极高 | Gartner、McKinsey、IDC、BCG |
| P1 | 上市公司财报/官方公告 | 高 | 年报、10-K、招股书 |
| P1 | 行业协会/标准组织 | 高 | IEEE、IETF、各行业协会 |
| P2 | 知名媒体深度报道 | 中高 | Reuters、Bloomberg、财新、36氪 |
| P2 | 技术官方文档/博客 | 中高 | 官方 docs、engineering blog |
| P3 | 统计数据平台 | 中 | Statista、Our World in Data |
| P3 | 研究机构/智库 | 中 | Brookings、RAND、中国信通院 |

---

## 2. 搜索策略

### 2.1 行业报告与市场数据

```
web_search("{行业} market size 2025 2026 report")
web_search("{行业} 市场规模 行业报告 2025")
web_search("{行业} industry analysis forecast")
web_search("site:mckinsey.com {关键词}")
web_search("site:gartner.com {关键词}")
```

**追溯原始来源**：很多文章引用了行业报告的数据但不给全文。当看到 "据 XX 报告显示" 时：
```
web_search("{报告标题} PDF download")
web_search("{报告标题} {发布机构} full report")
```

### 2.2 统计数据

**全球宏观数据**：
```
web_crawl("https://data.worldbank.org/indicator/{indicator_code}")
web_search("site:data.worldbank.org {关键词}")
web_search("site:stats.oecd.org {关键词}")
```

**中国数据**：
```
web_search("site:stats.gov.cn {关键词}")  # 国家统计局
web_search("site:caict.ac.cn {关键词}")   # 中国信通院
web_search("{关键词} 白皮书 PDF 2025 2026")
```

**科技行业数据**：
```
web_search("site:statista.com {关键词}")
web_search("site:ourworldindata.org {关键词}")
web_search("{关键词} benchmark comparison data")
```

### 2.3 技术调研

**官方文档与技术博客**：
```
web_search("{技术名} official documentation")
web_search("{技术名} vs {技术名} benchmark 2025 2026")
web_search("site:github.com {项目名} stars")
web_search("{技术名} engineering blog architecture")
```

**开源生态数据**：
```
web_crawl("https://api.github.com/repos/{owner}/{repo}")  # 获取 star 数、fork 数等
web_search("{技术} awesome list github")
web_search("{技术} adoption survey developer")
```

### 2.4 政策法规

```
web_search("{政策主题} 政策 法规 2025 2026")
web_search("{policy_topic} regulation legislation")
web_search("site:gov.cn {关键词}")
web_search("site:europa.eu {关键词}")
```

### 2.5 竞品/公司分析

```
web_search("{公司名} annual report 2025")
web_search("{公司名} 10-K SEC filing")
web_search("{产品} competitive landscape comparison")
web_search("{行业} top companies market share")
```

---

## 3. 深度抓取技巧

### 绕过摘要页获取全文

很多网站只展示摘要，全文需要进一步操作：

```
# 先抓取摘要页，从中找到全文链接
web_crawl("{article_url}")

# 找到全文 PDF 链接后下载
execute("wget -q '{pdf_url}' -O research_data/{filename}.pdf")
execute("pdftotext research_data/{filename}.pdf research_data/{filename}.txt")
```

### 多语言搜索

对于同一个主题，中英文搜索结果差异很大。两者都搜可以获得更全面的信息：

```
web_search("electric vehicle market 2025 global|电动汽车市场 2025 全球")
```

### 追溯数据引用链

当网页中出现 "据 XX 调查/报告显示，某某数据为 XX" 时，这个数据往往是二手引用。应追溯到原始来源：

1. 记录被引用的报告/调查名称和发布机构
2. `web_search("{报告名称} {机构} 原文 full report PDF")`
3. `web_crawl` 原始来源获取第一手数据

---

## 4. 数据提取规范

从抓取的内容中，重点提取以下类型的数据：

| 数据类型 | 示例 | 报告中的呈现方式 |
|---------|------|----------------|
| 市场规模 | "2025 年全球 XX 市场规模达 XXX 亿美元" | 表格 + 文中引用 |
| 增长率 | "年复合增长率(CAGR) 为 XX%" | 文中引用 |
| 市场份额 | "公司 A 占比 XX%，公司 B 占比 XX%" | 表格 |
| 技术指标 | "性能提升 XX%，延迟降低 XX ms" | 表格 + 对比分析 |
| 时间节点 | "预计 2027 年达到 XX" | 时间线描述 |
| 用户/采用率 | "日活用户 XXX 万，同比增长 XX%" | 文中引用 |

每个数据点必须标注来源：`[n]` 对应参考文献编号。

---

## 5. 引用格式

```json
[
  "McKinsey & Company. Report Title. Year. https://www.mckinsey.com/...",
  "国家统计局. 报告标题. 年份. https://stats.gov.cn/...",
  "Bloomberg. Article Title. Date. https://www.bloomberg.com/...",
  "GitHub Repository. {owner}/{repo}. Accessed {date}. https://github.com/..."
]
```
