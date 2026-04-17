---
name: github-trending
description: |
  获取 GitHub 最新热门开源项目。当用户说"GitHub热门项目"、"GitHub trending"、"最近热门开源项目"、"GitHub热门仓库"、"有什么热门开源项目"时触发此技能。支持按时间范围（每日/每周/每月）和编程语言筛选。输出项目名称、git链接、描述、star数量。
---

# GitHub 热门项目

获取 GitHub 最新热门开源项目，帮助用户快速了解当前最受关注的开源动态。

## 触发条件

当用户表达以下意图时使用此技能：
- "GitHub热门项目"、"GitHub trending"
- "最近热门开源项目"、"热门开源"
- "有什么热门的开源项目"
- "GitHub上什么项目火"
- "推荐一些热门开源项目"

## 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| since | 时间范围：`daily`（每日）、`weekly`（每周）、`monthly`（每月） | `daily` |
| language | 编程语言筛选，如 `python`、`javascript`、`rust` 等，留空为全部语言 | 空（全部） |

## 工作流程

### Step 1: 解析用户意图

从用户输入中提取参数：
- 时间范围：用户说"今天/每日"→ `daily`，"本周/这周"→ `weekly`，"本月/这个月"→ `monthly`。若未明确指定，默认 `daily`。
- 编程语言：用户说"Python热门"→ `python`，"Rust项目"→ `rust`。若未指定，默认为全部语言。

### Step 2: 获取热门项目数据

执行辅助脚本：

```bash
python3 <skill-path>/scripts/fetch_trending.py <since> <language>
```

示例：
```bash
# 获取每日热门（全部语言）
python3 /home/rainclaw/3ebjuci3jJWGDrs7NDr6ts/skills/github-trending/scripts/fetch_trending.py daily

# 获取每周 Python 热门
python3 /home/rainclaw/3ebjuci3jJWGDrs7NDr6ts/skills/github-trending/scripts/fetch_trending.py weekly python
```

脚本会输出 JSON 数组，每个元素包含：
- `name`: 项目全名（owner/repo）
- `url`: GitHub 链接
- `description`: 项目描述
- `stars`: Star 数量
- `language`: 主要编程语言
- `forks`: Fork 数量

### Step 3: 格式化输出

将获取到的数据以清晰的表格形式呈现给用户：

**输出格式模板**（MUST 遵循此格式）：

```
## 🔥 GitHub 热门项目（{时间范围} | {语言筛选}）

| # | 项目名称 | ⭐ Stars | 语言 | 描述 |
|---|---------|---------|------|------|
| 1 | [owner/repo](url) | 12,345 | Python | 项目描述 |
| 2 | [owner/repo](url) | 9,876 | Rust | 项目描述 |
| ... |

> 数据来源：GitHub Search API，按 Star 数降序排列
```

### Step 4: 补充说明（可选）

- 如果用户对某个项目感兴趣，可以结合 `read-github` 技能深入了解该项目
- 如果结果较少，建议用户扩大时间范围（如从 daily 改为 weekly）
- 如果 API 请求失败，提示用户稍后重试

## 注意事项

- GitHub Search API 有速率限制（未认证 10 次/分钟），避免频繁调用
- Star 数量为总量而非增量，API 不直接提供日增 Star 数据
- 如果用户指定了不常见的语言，可能返回较少结果，此时建议改用更宽泛的语言或去掉语言筛选
