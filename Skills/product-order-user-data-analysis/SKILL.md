---
name: product-order-user-data-analysis
description: "电商数据分析（商品/订单/用户三表分析）。当用户需要对商品表(products)、订单表(orders)、用户表(users)进行数据分析时触发此技能。支持根据用户问题动态生成分析脚本，涵盖：商品销售排行、库存预警、分类销售分析；用户消费排行、复购率、注册趋势；订单状态分布、销售额趋势、客单价分析；以及商品关联购买分析、用户品类偏好等交叉分析。输出包括：Markdown格式统计摘要。触发词包括：数据分析、电商分析、商品分析、订单分析、用户分析、销售分析、复购率、库存预警、商品排行、销售趋势、关联分析等。数据来源为PostgreSQL数据库，数据源地址通过动态变量从agent记忆中获取。"
---

# product-order-user-data-analysis

电商三表（商品/订单/用户）数据分析技能。

## 触发条件

当用户提到以下任一场景时，必须使用此技能：
- 对商品表(products)、订单表(orders)、用户表(users)做数据分析
- 电商/零售类的数据分析和报表需求
- 需要商品排行、订单趋势、用户画像等分析
- 需要从数据库中提取数据并生成统计报表
- 用户提到了"商品、订单、用户"三表分析

## 数据来源

**数据源类型**：仅支持 PostgreSQL 数据库

**数据源配置**：PostgreSQL 连接信息通过工具`get_datasource_by_code("product_order_users")`根据场景编码code为product_order_users获取数据源信息。动态变量格式如下：

```json
{
  "host": "数据库主机地址",
  "port": "端口",
  "database": "数据库名",
  "username": "用户名",
  "password": "密码"
}
```

## 数据表结构与关系

### 表关系概览

三张表通过外键建立关联关系，构成完整的电商数据模型：

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ER 关系图                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐  │
│   │   products   │        │    orders    │        │    users     │  │
│   │   (商品表)    │        │    (订单表)   │        │    (用户表)   │  │
│   ├──────────────┤        ├──────────────┤        ├──────────────┤  │
│   │ product_id PK├───────►│ product_id FK│        │ user_id  PK  │  │
│   │ product_name │        │ user_id    FK├───────►│ username     │  │
│   │ category     │        │ quantity     │        │ phone        │  │
│   │ price        │        │ unit_price   │        │ registration │  │
│   │ stock        │        │ total_amount │        │              │  │
│   └──────────────┘        │ order_time   │        └──────────────┘  │
│                           │ status       │                          │
│                           │ address      │                          │
│                           └──────────────┘                          │
│                                                                     │
│   关系说明:                                                          │
│   • users 1:N orders  (一个用户可以有多个订单)                        │
│   • products 1:N orders (一个商品可以出现在多个订单中)                  │
│   • orders 是关联 users 和 products 的中间表                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 表关系详细说明

| 关系类型 | 主表 | 从表 | 关联字段 | 业务含义 |
|----------|------|------|----------|----------|
| 1:N | users | orders | user_id | 一个用户可创建多个订单 |
| 1:N | products | orders | product_id | 一个商品可被多次购买 |

### 数据流向

```
用户注册 → users表 → 创建订单 → orders表 → 关联商品 → products表
    │                        │
    └────────────────────────┘
            查询订单历史
```

### products（商品表）
| 字段 | 类型 | 约束 | 语义 |
|------|------|------|------|
| product_id | VARCHAR(20) | PK | 商品ID，如 P0001 |
| product_name | VARCHAR(100) | NOT NULL | 商品名称 |
| category | VARCHAR(50) | - | 商品分类 |
| price | DECIMAL(10,2) | NOT NULL | 单价(元) |
| stock | INT | NOT NULL | 库存数量 |

### users（用户表）
| 字段 | 类型 | 约束 | 语义 |
|------|------|------|------|
| user_id | VARCHAR(20) | PK | 用户ID，如 U0001 |
| username | VARCHAR(50) | NOT NULL | 用户名 |
| phone | VARCHAR(20) | UNIQUE | 手机号 |
| registration_time | DATE | NOT NULL | 注册日期 |

### orders（订单表）
| 字段 | 类型 | 约束 | 语义 |
|------|------|------|------|
| order_id | VARCHAR(20) | PK | 订单ID，如 O0001 |
| user_id | VARCHAR(20) | FK→users | 用户ID |
| product_id | VARCHAR(20) | FK→products | 商品ID |
| quantity | INT | NOT NULL | 购买数量 |
| unit_price | DECIMAL(10,2) | NOT NULL | 购买单价 |
| total_amount | DECIMAL(10,2) | NOT NULL | 订单金额 |
| order_time | TIMESTAMP | - | 下单时间 |
| status | VARCHAR(20) | - | 订单状态 |
| address | VARCHAR(200) | - | 收货地址 |

### 订单状态机

订单状态流转遵循以下状态机：

```
待支付 → 已支付 → 已发货 → 已完成
   │          │
   └──────────└→ 已取消
```

#### 状态说明

| 状态 | 描述 | 触发条件 | 后续状态 |
|------|------|----------|----------|
| **待支付** | 用户提交订单，等待支付 | 用户提交订单 | 已支付、已取消 |
| **已支付** | 用户完成支付，订单待发货 | 用户支付成功 | 已发货、已取消 |
| **已发货** | 商家已发货，等待收货 | 商家发货操作 | 已完成、已取消 |
| **已完成** | 用户确认收货，订单结束 | 用户确认收货 | - |
| **已取消** | 订单被取消 | 用户取消/超时/商家取消 | - |

#### 状态流转规则

```
1. 待支付 → 已支付：用户完成支付
2. 待支付 → 已取消：用户取消或支付超时
3. 已支付 → 已发货：商家执行发货
4. 已支付 → 已取消：用户申请退款且商家同意
5. 已发货 → 已完成：用户确认收货
6. 已发货 → 已取消：售后退货流程完成
```

#### 状态查询 SQL

```python
# 查询各状态订单数量
query = """
SELECT status, COUNT(*) AS order_count, 
       SUM(total_amount) AS total_sales,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) AS percentage
FROM orders
GROUP BY status
ORDER BY 
    CASE status 
        WHEN '待支付' THEN 1 
        WHEN '已支付' THEN 2 
        WHEN '已发货' THEN 3 
        WHEN '已完成' THEN 4 
        WHEN '已取消' THEN 5 
    END
"""
```

## AI 动态脚本生成流程

### Step 1: 理解用户需求
分析用户问题，提取关键信息：
- **实体识别**：确定涉及的业务实体（商品、订单、用户）
- **分析类型**：确定分析方式（排行、趋势、分布、预警、关联、偏好）
- **参数提取**：提取具体参数（TOP N、阈值、时间范围等）

### Step 2: 生成 SQL 查询语句
根据用户需求动态生成针对性的 SQL 查询：

**示例1：库存预警**
```python
# 用户问题：库存预警
query = """
SELECT product_id, product_name, category, price, stock 
FROM products 
WHERE stock < 10 
ORDER BY stock ASC
"""
```

**示例2：商品销售排行 TOP10**
```python
# 用户问题：商品销售排行TOP10
query = """
SELECT p.product_id, p.product_name, p.category, 
       SUM(o.quantity) AS total_quantity, 
       SUM(o.total_amount) AS total_sales
FROM products p
LEFT JOIN orders o ON p.product_id = o.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_sales DESC
LIMIT 10
"""
```

**示例3：用户复购率分析**
```python
# 用户问题：用户复购率
query = """
WITH user_orders AS (
    SELECT user_id, COUNT(order_id) AS order_count 
    FROM orders GROUP BY user_id
)
SELECT 
    ROUND(COUNT(CASE WHEN order_count >= 2 THEN 1 END) * 100.0 / COUNT(*), 2) AS repurchase_rate,
    COUNT(*) AS total_users,
    COUNT(CASE WHEN order_count >= 2 THEN 1 END) AS repurchased_users
FROM user_orders
"""
```

**示例4：销售趋势**
```python
# 用户问题：销售趋势
query = """
SELECT 
    order_time::DATE AS order_date,
    COUNT(*) AS order_count,
    SUM(total_amount) AS daily_sales
FROM orders
GROUP BY order_time::DATE
ORDER BY order_date
"""
```

### Step 3: 编写临时分析脚本
生成完整的 Python 分析脚本，包含：
- 数据库连接配置
- SQL 查询执行
- 结果格式化输出
- Markdown 报告生成

```python
import psycopg2
from datetime import datetime

def analyze():
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        dbname=database
    )
    
    cursor = conn.cursor()
    
    # 执行动态生成的查询
    cursor.execute(generated_query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # 生成 Markdown 表格
    md = f"## 分析结果\n\n"
    md += f"| {' | '.join(columns)} |\n"
    md += f"| {' | '.join(['---'] * len(columns))} |\n"
    for row in rows:
        md += f"| {' | '.join(str(c) for c in row)} |\n"
    
    print(md)
    cursor.close()
    conn.close()

if __name__ == '__main__':
    analyze()
```

### Step 4: 执行脚本并返回结果
- 执行临时生成的 Python 脚本
- 获取数据库查询结果
- 格式化为 Markdown 表格输出

### Step 5: 输出交付
将分析结果以 Markdown 格式呈现给用户，包含：
- 分析标题
- 数据表格
- 统计摘要（如适用）

## 问题解析规则

### 实体识别

| 实体 | 关键词 | 对应的表 |
|------|--------|----------|
| product | 商品、产品、货品、库存、品类、价格、销售排行、热销 | products |
| order | 订单、下单、购买、销售额、成交、客单价、状态、退款、取消 | orders |
| user | 用户、会员、客户、复购、注册、消费、活跃、新用户、老用户 | users |

### 分析类型识别

| 类型 | 关键词 | 典型 SQL 模式 |
|------|--------|--------------|
| ranking | 排行、排名、top、TOP、前、最高、最多 | ORDER BY ... DESC LIMIT N |
| trend | 趋势、变化、走势、增长、下降、环比、同比 | GROUP BY 时间字段 ORDER BY 时间 |
| distribution | 分布、占比、比例、结构、构成 | GROUP BY 分类字段 + 百分比计算 |
| alert | 预警、提醒、低于、不足、紧缺 | WHERE 条件筛选 |
| association | 关联、一起、搭配、组合、推荐 | JOIN 多表 + 聚合统计 |
| preference | 偏好、喜欢、倾向、习惯 | GROUP BY 用户 + 分类统计 |

### 参数提取规则

| 参数类型 | 匹配模式 | 示例 |
|----------|----------|------|
| TOP N | `TOP数字`、`top数字`、`前数字` | TOP10、top5、前20 |
| 阈值 | `低于数字`、`少于数字`、`不足数字` | 低于10、少于5 |
| 时间范围 | `近N天`、`过去N周`、`最近N月` | 近7天、过去2周 |

## 分析场景与 SQL 模板映射

### 商品分析
| 场景 | SQL 模板 |
|------|----------|
| 商品销售排行 | `SELECT p.*, SUM(o.total_amount) FROM products p LEFT JOIN orders o ON ... GROUP BY ... ORDER BY total_sales DESC LIMIT N` |
| 库存预警 | `SELECT * FROM products WHERE stock < threshold ORDER BY stock ASC` |
| 品类销售分析 | `SELECT category, SUM(total_amount), COUNT(*) FROM products p JOIN orders o ON ... GROUP BY category` |
| 价格分布 | `SELECT price_range, COUNT(*) FROM products GROUP BY price_range ORDER BY MIN(price)` |

### 用户分析
| 场景 | SQL 模板 |
|------|----------|
| 用户消费排行 | `SELECT u.*, SUM(o.total_amount) FROM users u LEFT JOIN orders o ON ... GROUP BY ... ORDER BY total DESC LIMIT N` |
| 复购率分析 | `WITH user_orders AS (SELECT user_id, COUNT(*) FROM orders GROUP BY user_id) SELECT ROUND(COUNT(CASE WHEN count>=2 THEN 1 END)*100/COUNT(*),2) AS repurchase_rate FROM user_orders` |
| 注册趋势 | `SELECT registration_time, COUNT(*) FROM users GROUP BY registration_time ORDER BY registration_time` |
| 新老用户对比 | `WITH first_order AS (SELECT user_id, MIN(order_time) FROM orders GROUP BY user_id) SELECT CASE WHEN o.order_time=first_order THEN '新用户' ELSE '老用户' END, COUNT(*), SUM(total_amount) FROM orders o JOIN first_order ON ... GROUP BY user_type` |

### 订单分析
| 场景 | SQL 模板 |
|------|----------|
| 订单状态分布 | `SELECT status, COUNT(*), SUM(total_amount), ROUND(COUNT(*)*100/(SELECT COUNT(*) FROM orders),2) FROM orders GROUP BY status` |
| 销售趋势 | `SELECT order_time::DATE, COUNT(*), SUM(total_amount) FROM orders GROUP BY order_time::DATE ORDER BY order_date` |
| 客单价分析 | `SELECT CASE WHEN total_amount < 50 THEN '0-50' ... END AS range, COUNT(*), SUM(total_amount) FROM orders GROUP BY range` |
| 异常订单率 | `SELECT status, COUNT(*), ROUND(COUNT(*)*100/(SELECT COUNT(*) FROM orders),2) FROM orders WHERE status IN ('已取消','待支付') GROUP BY status` |

### 交叉分析
| 场景 | SQL 模板 |
|------|----------|
| 商品关联分析 | `SELECT a.product_id, b.product_id, COUNT(*) FROM orders a JOIN orders b ON a.user_id=b.user_id AND a.order_id=b.order_id AND a.product_id<b.product_id GROUP BY a.product_id, b.product_id HAVING COUNT(*)>=min_occur ORDER BY COUNT(*) DESC LIMIT 20` |
| 用户品类偏好 | `SELECT u.user_id, p.category, COUNT(*), SUM(o.total_amount) FROM users u JOIN orders o ON ... JOIN products p ON ... GROUP BY u.user_id, p.category ORDER BY total_spent DESC` |
| 订单时段分布 | `SELECT EXTRACT(HOUR FROM order_time)::INT AS hour, COUNT(*), SUM(total_amount) FROM orders GROUP BY hour ORDER BY hour` |

## 输出格式说明

### Markdown 输出
- 分析结果以 Markdown 表格形式输出
- 包含分析标题和统计摘要
- 支持分页显示（超过15条时提示）
- 示例输出：

```markdown
## 📊 库存预警分析

| product_id | product_name | category | price | stock |
|------------|--------------|----------|-------|-------|
| P001 | 商品A | 电子产品 | 199.00 | 3 |
| P002 | 商品B | 服装 | 99.00 | 5 |

**统计摘要**
- 预警商品数：2
- 最低库存：3
```

## 依赖与环境

### 所需 Python 库
```bash
pip install psycopg2-binary  # PostgreSQL 驱动
```

### 环境变量配置
```bash
export HOST=数据库地址
export PORT=端口
export USERNAME=用户名
export PASSWORD=密码
export DATABASE=数据库名
```

## 技能使用示例

### 示例1：库存预警
**用户问题**：库存预警
**生成分析**：查询库存低于10的商品
**输出**：商品列表表格 + 统计摘要

### 示例2：商品销售排行
**用户问题**：商品销售排行TOP5
**生成分析**：按销售额排序的TOP5商品
**输出**：TOP5商品表格

### 示例3：用户复购率
**用户问题**：用户复购率是多少
**生成分析**：计算购买2次及以上用户的占比
**输出**：复购率数值 + 用户分布

### 示例4：销售趋势
**用户问题**：最近一周的销售趋势
**生成分析**：按日统计销售额和订单数
**输出**：每日销售数据表格

### 示例5：交叉分析
**用户问题**：哪些商品经常一起购买
**生成分析**：商品关联购买分析
**输出**：商品组合列表 + 共同购买次数

## 注意事项

1. **SQL 注入防护**：所有动态参数必须使用参数化查询，禁止字符串拼接
2. **性能优化**：对于大数据量，考虑添加索引和分页限制
3. **错误处理**：捕获数据库连接异常和查询异常，返回友好提示
4. **数据脱敏**：输出结果中隐藏敏感信息（如完整手机号）
5. **权限控制**：确保数据库用户仅有只读权限