---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-core-experience', 'step-04-emotional-response', 'step-05-inspiration', 'step-06-design-system', 'step-07-defining-experience', 'step-08-visual-foundation', 'step-09-design-directions', 'step-10-user-journeys', 'step-11-component-strategy', 'step-12-ux-patterns', 'step-13-responsive-accessibility', 'step-14-complete']
inputDocuments: ['prd.md']
---

# UX Design Specification RainClaw

**Author:** 老GO
**Date:** 2026-05-09

---

## Executive Summary

### Project Vision
RainClaw 平台数据库源配置功能，为管理员提供 Web 界面管理 MySQL、PostgreSQL、Oracle、MongoDB、SQL Server 五种数据库的连接信息，以唯一编码标识分类存储。

### Target Users
平台管理员 — 需要为不同业务场景配置数据库连接供 AI Agent 后续使用。

### Key Design Challenges
1. 表单字段较多（名称、主机、端口、库名、账号、密码、数据库类型、场景标签），需合理布局
2. 左侧菜单入口需融入现有菜单体系，风格一致
3. 密码字段需要显示/隐藏切换

### Design Opportunities
- 编码字段输入时校验唯一性，避免重复
- 数据库类型用图标标识，增强辨识度

## Core User Experience

### Defining Experience
数据源配置页面的核心操作包括数据源的增删改查。管理员通过左侧菜单进入管理页面，以表格形式查看所有数据源，支持新增、编辑、删除。

### Platform Strategy
- **平台：** Web 端，RainClaw 平台内嵌页面
- **交互方式：** 鼠标/键盘，标准表单操作
- **设备：** 桌面端为主
- **离线功能：** 不需要

### Effortless Interactions
- 新增/编辑表单字段一行两个，减少滚动
- 数据库类型以下拉选择，避免手动输入错误
- 密码字段回显明文，编辑时无需重复填写
- 编码字段唯一，新增时校验不重复

### Experience Principles
1. **效率优先：** 增删改查操作直白，最少点击完成
2. **信息透明：** 列表直接展示全部关键信息（名称、编码、类型、主机、端口、用户名、密码）
3. **风格一致：** 完全沿用 RainClaw 现有 UI 风格，不引入新设计语言

### User Mental Model

- **已有认知：** 管理员对"表格列表 + 新增/编辑表单"的模式非常熟悉，这是后台管理的通用范式
- **预期：** 进入页面后看到所有已配数据源，能快速找到目标数据源进行编辑或删除
- **可能的困惑点：** 密码字段编辑时的处理（已确定为回显明文）、编码唯一性校验

### Success Criteria

- 管理员首次使用就能独立完成数据源配置，无需指导
- 新增一个数据源从点击"新增"到保存成功不超过 30 秒
- 列表页一眼看清所有数据源的关键信息（名称、编码、类型、主机）
- 编辑时无需重复填写密码（已回显明文）

### Novel UX Patterns

采用成熟 CRUD 模式，无创新交互需求：
- **表格查看：** 直接采用标准表格布局
- **弹窗/页面表单：** 按 RainClaw 现有表单风格
- **下拉选择数据库类型：** 标准下拉组件
- **编码输入：** 文本输入 + 唯一性校验

### Experience Mechanics

**1. 进入页面：**
- 左侧菜单点击"数据源配置" → 进入列表页
- 列表展示所有数据源，表格列：名称、编码、类型、主机、端口、用户名、密码、操作

**密码列交互：**
- 默认显示 `***`，旁边有眼睛图标
- 点击眼睛图标切换明文/掩码显示
- 与表单中的密码字段显示/隐藏逻辑一致

**2. 新增数据源：**
- 点击"新增"按钮 → 弹出 Modal 对话框
- 填写：名称、编码、主机、端口、库名、账号、密码、数据库类型（下拉）
- 字段一行两个，减少滚动
- 点击"保存" → 列表刷新显示新数据源

**3. 编辑数据源：**
- 点击列表中"编辑" → 弹出 Modal 对话框，回填所有字段（密码明文回显）
- 修改后点击"保存" → 列表更新

**4. 删除数据源：**
- 点击列表中"删除" → 确认对话框 → 确认后删除并刷新列表

**5. 按名称模糊查询：**
- 列表上方提供名称搜索输入框 + 查询/重置按钮
- 输入名称关键字，点击"查询" → 列表过滤匹配的数据源
- 点击"重置" → 清空搜索条件，恢复全量列表

## Desired Emotional Response

### Primary Emotional Goals
- **高效省心：** 操作直白流畅，管理员快速完成配置不拖沓
- **清晰可控：** 数据源列表一目了然，每个数据源的用途（标签）和状态清晰可辨

### Emotional Journey Mapping
- **首次使用：** 进入页面后立刻理解"这是个配置管理工具"
- **操作中：** 表单填写自然顺畅，不困惑
- **完成后：** 确认数据源已保存，下次回来直接能看到

### Emotional Design Principles
- 不搞花哨动画，追求响应快速、信息明确
- 减少认知负担，字段标签清晰，操作按钮位置符合预期

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis
设计灵感直接来源于 RainClaw 平台自身。现有左侧菜单体系、页面布局、配色方案和交互模式均已成熟，本功能完全沿用现有设计语言。

### Design Inspiration Strategy
- **直接复用：** 左侧菜单样式、页面容器布局、按钮风格、表格样式
- **无需引入：** 不引入新的 UI 框架或设计语言

## Design System Foundation

### 1.1 Design System Choice

直接沿用 RainClaw 现有设计体系（Tailwind CSS + 现有 Vue 组件模式），不引入新的 UI 框架。

### Rationale for Selection

- **风格一致原则：** UX 设计规范已确立"风格一致"为核心体验原则
- **棕地项目特性：** 现有 RainClaw 组件体系已成熟，直接复用成本最低
- **内部管理工具定位：** 无需独立品牌视觉
- **开发效率：** 直接使用现有 Tailwind CSS 和 Vue 组件，开发速度最快

### Implementation Approach

- **布局：** 复用现有页面容器布局（左侧菜单 + 右侧内容区）
- **表格：** 使用现有表格组件样式展示数据源列表
- **表单：** 使用现有表单组件样式（输入框、下拉选择、按钮）
- **菜单：** 在现有左侧菜单中新增"数据源配置"入口，风格与现有菜单项一致
- **按钮：** 沿用现有按钮风格

### Customization Strategy

页面内部布局根据功能需要微调（如表单字段一行两个），颜色、字体、间距、圆角等视觉 tokens 完全沿用现有平台值。

## Visual Design Foundation

### Color System

完全沿用 RainClaw 现有配色方案，不引入新颜色。按钮、链接、警告、表格行等语义色直接复用平台现有 tokens。

### Typography System

完全沿用 RainClaw 现有字体体系（字体族、字号层级、行高），不引入新字体。

### Spacing & Layout Foundation

- 复用现有页面容器布局（左侧菜单 + 右侧内容区）
- 表单内部字段间距、表格行列间距、按钮间距等均沿用平台现有 spacing 规范
- 不做自定义间距设计

### Accessibility Considerations

- 跟随 RainClaw 平台现有的可访问性标准
- 密码切换图标需有足够的点击区域（建议 32x32px 以上）
- 表格文字对比度符合 WCAG AA 标准（现有平台已满足）

## Design Direction Decision

### Design Directions Explored

由于完全沿用 RainClaw 现有设计体系，仅探索了一个设计方向——直接复用现有平台风格，不创建独立的设计变体。

### Chosen Direction

**直接沿用 RainClaw 现有 UI 风格**，仅在页面内部布局上做功能适配。

### Design Rationale

- 棕地项目，平台设计语言已成熟稳定
- 内部管理工具无需独立品牌视觉
- 开发效率最高，无需学习或引入新框架

### Key Layout Decisions

1. **新增/编辑使用 Modal 弹窗** — 不跳转页面，操作更连贯
2. **列表包含列：** 名称、编码、类型、主机、端口、用户名、密码、操作
3. **密码列默认显示 `***`**，点击眼睛图标切换明文
4. **编码字段唯一**，新增时需校验不重复
5. **按名称模糊查询**，带查询/重置按钮
6. **字段一行两个**，减少滚动

## User Journey Flows

### Journey 1: 新增数据源

```mermaid
flowchart TD
    A[点击左侧菜单"数据源配置"] --> B[进入数据源列表页]
    B --> C[点击"新增数据源"按钮]
    C --> D[弹出 Modal 表单]
    D --> E[填写字段：名称、编码、主机、端口、库名、账号、密码、数据库类型]
    E --> F[点击"保存"]
    F --> G{编码是否唯一?}
    G -->|不唯一| H[提示"编码已存在"]
    H --> E
    G -->|唯一| I[保存成功]
    I --> J[列表刷新，显示新数据源]
```

### Journey 2: 查看与搜索数据源

```mermaid
flowchart TD
    A[进入数据源列表页] --> B[查看表格展示所有数据源]
    B --> C{需要查找特定数据源?}
    C -->|是| D[在搜索框输入名称关键字]
    D --> E[点击"查询"]
    E --> F[列表过滤匹配结果]
    F --> G{结果满意?}
    G -->|是| H[查看/操作数据源]
    G -->|否| I[点击"重置"]
    I --> B
    C -->|否| H
```

### Journey 3: 编辑数据源

```mermaid
flowchart TD
    A[列表中找到目标数据源] --> B[点击"编辑"]
    B --> C[弹出 Modal 表单，回填所有字段]
    C --> D[密码明文回显]
    D --> E[修改需要变更的字段]
    E --> F[点击"保存"]
    F --> G{编码是否与其他重复?}
    G -->|重复| H[提示"编码已存在"]
    H --> E
    G -->|唯一或无变化| I[更新成功]
    I --> J[列表刷新显示更新后的数据]
```

### Journey 4: 删除数据源

```mermaid
flowchart TD
    A[列表中找到目标数据源] --> B[点击"删除"]
    B --> C[弹出确认对话框]
    C --> D{确认删除?}
    D -->|否| E[取消，返回列表]
    D -->|是| F[删除成功]
    F --> G[列表刷新，数据源消失]
```

### Flow Optimization Principles

- **最小步骤完成：** 新增从点击到保存最多 3 步（点按钮→填表单→保存）
- **即时反馈：** 编码唯一性提交时校验，不延迟到保存后才发现错误
- **密码友好：** 编辑时明文回显，避免管理员忘记密码需重新配置
- **非破坏性操作：** 删除前必须二次确认，防止误删

## Component Strategy

### Design System Components

所有所需组件均可从 RainClaw 现有组件库直接复用：

| 组件 | 用途 | 来源 |
|------|------|------|
| 表格 | 展示数据源列表 | 现有组件 |
| Modal 弹窗 | 新增/编辑表单容器 | 现有组件 |
| 表单输入框 | 名称、编码、主机、端口、库名、账号、密码 | 现有组件 |
| 下拉选择框 | 数据库类型选择 | 现有组件 |
| 按钮 | 新增/保存/取消/查询/重置/删除 | 现有组件 |
| 确认对话框 | 删除确认 | 现有组件 |
| 搜索输入框 | 名称模糊查询 | 现有组件 |

### Custom Components

无需自定义组件。密码列的显示/隐藏切换可复用表单中已有的密码显隐组件。

### Component Implementation Strategy

零自定义组件开发，直接使用现有组件搭建页面。页面布局按功能需求组合（查询栏 + 表格 + Modal 表单）。

### Implementation Roadmap

单次完成，不分阶段：
1. 搭建列表页（表格 + 查询栏）
2. 搭建 Modal 表单（复用现有表单组件）
3. 集成 API 对接 CRUD

## UX Consistency Patterns

### Button Hierarchy

沿用 RainClaw 现有按钮层级：
- **主要操作：** 新增、保存 — 品牌色填充按钮
- **次要操作：** 取消、重置 — 边框或文字按钮
- **危险操作：** 删除 — 红色按钮（触发前先弹出确认对话框）

### Feedback Patterns

- **操作成功：** Toast 提示"保存成功"/"删除成功"，短暂自动消失
- **操作失败：** Toast 提示错误信息
- **删除确认：** Modal 确认对话框，防止误操作
- **编码重复：** 表单内联提示"编码已存在"，不提交

### Form Patterns

- 字段一行两个，以 grid 布局排列
- 数据库类型用下拉选择，减少输入错误
- 密码明文回显（编辑时），无需重复填写
- 编码唯一性在提交时校验
- 必填字段标记（*）

### Navigation Patterns

- 左侧菜单"数据源配置"入口，点击进入列表页
- 新增/编辑不跳转页面，使用 Modal 弹窗
- 列表内操作（编辑/删除）直接在行内触达

### Additional Patterns

- **空状态：** 无数据源时，列表显示"暂无数据源，点击新增"
- **编码唯一性：** 提交时后端校验，前端展示对应错误提示
- **密码显隐：** 列表和表单中均支持切换显示/隐藏

## Responsive Design & Accessibility

### Responsive Strategy

桌面端优先，不做移动端适配。数据源配置是平台内部管理功能，管理员通过桌面浏览器使用。

### Accessibility Strategy

跟随 RainClaw 平台现有可访问性标准：
- 密码切换图标点击区域 ≥ 32x32px
- 表单字段标签清晰，与输入框正确关联
- 操作按钮文案明确
- 错误提示直观可见

### Implementation Guidelines

- 复用 RainClaw 现有页面容器布局
- 表单使用 grid 一行两列布局
- 表格不设固定列宽，内容自适应
- 随平台整体做暗色模式（如平台已支持）
