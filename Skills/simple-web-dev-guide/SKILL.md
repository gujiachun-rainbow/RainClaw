---
name: simple-web-dev-guide
description: 轻量级网站/应用开发指南。适用于搭建各类Web系统、数据分析报表、数据管理后台、数据增删改查功能。包含完整项目结构、前端HTML/JS/Vue、后端Python FastAPI+SQLite的开发指引与代码模板。
---

# 简单Web项目开发规范

## 快速开始

### 1. 项目结构

**⚠️ 强制约束：所有项目文件必须放在一个独立的文件夹目录下，避免与其他文件耦合。**

```
my-project/                 # 项目根目录（所有文件必须放在此目录下）
├── frontend/              # 前端文件
│   ├── index.html         # 主页面
│   ├── css/              # 样式
│   ├── js/               # 脚本
│   └── assets/            # 静态资源
├── backend/              # 后端API
│   ├── main.py            # FastAPI入口
│   ├── models.py         # 数据模型
│   ├── database.py       # SQLite连接
│   └── api/             # API路由
└── requirements.txt       # Python依赖（可选）
```

**目录约束说明：**
- 项目必须包含在一个独立的根目录下（如 `my-project/`）
- 所有源代码、配置文件、资源文件都必须放在该目录内
- 禁止将文件直接放在工作空间根目录或与其他项目混合
- 禁止在项目目录外创建依赖文件或临时文件

### 2. 技术选型优先级

**前端**：

- 首选：原生HTML + JS + CSS
- 备选：Vue 3（ CDN引入，方便快速上手）
- 备选：React（仅复杂交互时）

**后端**：

- 首选：Python + FastAPI
- 无特殊需求不选其他框架

**数据库**：

- 首选：SQLite（单文件，无需配置）
- 仅在需要多用户并发时考虑PostgreSQL/MySQL

### 3. 不需要Git

项目文件直接本地管理，无需版本控制。

## 前端开发

### 🎨 UI 设计原则

**默认推荐风格**：整体以白色为主色调，搭配简洁的灰色系文字，配合一两种鲜明的点缀色（如蓝色、绿色或橙色），打造清新、专业的视觉效果。

在开发前端 UI 界面时，必须参考 `./references/frontend-design.md` 的设计理念，打造独特、高质量的用户界面：

1. **先确定设计方向**：在开始编码前，明确界面的用途、目标用户和整体风格基调（极简主义、复古未来主义、有机自然风、奢华精致风等）
2. **默认配色方案**：白色背景 (#FFFFFF) + 深灰文字 (#333333) + 浅灰辅助文字 (#666666) + 主色调点缀（如蓝色 #1E90FF 或绿色 #00CED1）
3. **拒绝通用 AI 审美**：避免过度使用的字体（Inter、Roboto、Arial）、陈词滥调的配色（特别是白色背景配紫色渐变）、可预测的布局
4. **注重细节设计**：
   - 字体选择：独特、有个性的字体，而非通用字体
   - 色彩主题：使用 CSS 变量保持一致性，主色配鲜明点缀色
   - 动画效果：页面加载、滚动触发、悬停状态的惊喜效果
   - 空间构图：非对称布局、重叠元素、斜线流动、打破网格
   - 背景细节：渐变网格、噪点纹理、几何图案、分层透明、戏剧阴影

### 简单页面模板（HTML+JS）

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>我的应用</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div id="app">
        <h1>欢迎</h1>
        <button id="btn">点击</button>
    </div>
    <script src="js/app.js"></script>
</body>
</html>
```

### 数据请求

```javascript
// 简便API调用
// 同一个容器内：用相对路径或localhost
const API_BASE = '';  // 相对路径，生产环境可换成实际地址

async function callApi(endpoint, data) {
    const res = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    return res.json();
}
```

### 本地开发 vs 生产

```javascript
// 开发环境：后端在不同端口
const API_BASE = 'http://localhost:8000';

// 生产环境（Docker同一容器）：用相对路径
// const API_BASE = '';
```

### Vue 3 CDN快速上手

```html
<script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
<script>
const { createApp, ref } = Vue;
createApp({
    setup() {
        const message = ref('Hello');
        return { message };
    }
}).mount('#app');
</script>
```

### 前端调用后端API

前端访问后端API的两种方式：

**方式1：相对路径（推荐，同一容器内）**

```javascript
const API_BASE = '';  // 用相对路径

// 调用
async function getItems() {
    const res = await fetch(API_BASE + '/api/items');
    return res.json();
}

async function createItem(name) {
    const res = await fetch(API_BASE + '/api/items', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name})
    });
    return res.json();
}
```

**方式2：完整URL（本地开发）**

```javascript
const API_BASE = 'http://localhost:8000';  // 本地开发

// 调用
async function getItems() {
    const res = await fetch(API_BASE + '/api/items');
    return res.json();
}
```

### 完整前端页面示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>我的应用</title>
</head>
<body>
    <div id="app">
        <h1>物品管理</h1>
        <input v-model="newItem" @keyup.enter="addItem" placeholder="输入名称">
        <button @click="addItem">添加</button>
        <ul>
            <li v-for="item in items">{{ item.name }}</li>
        </ul>
    </div>

    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <script>
    const { createApp, ref, onMounted } = Vue;
    const API_BASE = '';  // 同容器用相对路径

    createApp({
        setup() {
            const items = ref([]);
            const newItem = ref('');

            const loadItems = async () => {
                const res = await fetch(API_BASE + '/api/items');
                items.value = await res.json();
            };

            const addItem = async () => {
                if (!newItem.value) return;
                await fetch(API_BASE + '/api/items', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({name: newItem.value})
                });
                newItem.value = '';
                await loadItems();
            };

            onMounted(() => {
                loadItems();
            });

            return { items, newItem, addItem };
        }
    }).mount('#app');
    </script>
</body>
</html>
```

## 后端开发

### FastAPI最小模板

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SQLite连接
def get_db():
    conn = sqlite3.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/hello")
def hello():
    return {"message": "你好"}
```

### 创建数据库表

```python
import sqlite3

def init_db():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
```

### API路由示例

```python
@app.post("/api/items")
def create_item(item: dict):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (name) VALUES (?)", (item['name'],))
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, "name": item['name']}

@app.get("/api/items")
def list_items():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items ORDER BY created_at DESC")
    items = cursor.fetchall()
    conn.close()
    return [{"id": r['id'], "name": r['name']} for r in items]
```

## 快速启动

### 前端

直接用浏览器打开 `frontend/index.html`

或使用简单HTTP服务器：

```bash
# Python 3
python -m http.server 8080 --directory frontend
```

### 后端

```bash
# 安装依赖
pip install fastapi uvicorn

# 启动
uvicorn main:app --reload --port 8000
```

## 检查清单

- [ ] 项目结构清晰，分离前后端目录
- [ ] 前端优先使用原生HTML/JS，只有复杂交互才用Vue/React
- [ ] 后端使用FastAPI + SQLite组合
- [ ] 避免引入不必要的依赖库
- [ ] 不需要Git管理，本地保存即可
- [ ] 用浏览器直接打开HTML即可预览前端
- [ ] 后端用 `uvicorn backend.main:app` 启动（保持与Docker一致）

## ⚠️ 重要开发规范：模块导入路径

### 问题背景

当使用 Docker 部署时，uvicorn 以模块路径方式启动：
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

这意味着：
- Python 工作目录是 `/app`（不是 `/app/backend`）
- `main.py` 位于 `/app/backend/main.py`
- 因此 `from database import` 找不到 `/app/database.py`

### ✅ 正确写法

```python
# main.py 位于 /app/backend/main.py
# database.py 位于 /app/backend/database.py

# ✅ 正确：用包路径前缀
from backend.database import get_db, init_db

# ❌ 错误：假设工作目录是 /app/backend
from database import get_db, init_db
```

### 判断规则

| uvicorn 启动方式                   | main.py 位置               | 正确 import                        |
| ------------------------------ | -------------------------- | -------------------------------- |
| `uvicorn main:app`             | `/app/main.py`             | `from database import`           |
| `uvicorn backend.main:app`     | `/app/backend/main.py`     | `from backend.database import`   |
| `uvicorn backend.api.main:app` | `/app/backend/api/main.py` | `from backend.api.models import` |

### ⚠️ 本地开发注意

**必须统一使用模块路径方式启动**，否则本地开发和 Docker 部署的 import 行为会不一致：

```bash
# ✅ 推荐：项目根目录下运行（与 Docker 行为一致）
uvicorn backend.main:app --reload --port 8000

# ❌ 不推荐：进入 backend 目录运行（与 Docker 行为不同）
# cd backend && uvicorn main:app
```

## 文件上传

### 前端

```html
<input type="file" id="fileInput">
<button onclick="uploadFile()">上传</button>

<script>
async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];
    if (!file) return alert('请选择文件');

    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData
    });
    const data = await res.json();

    if (data.success) {
        alert('上传成功: ' + data.filename);
    } else {
        alert('上传失败');
    }
}
</script>
```

### 后端

```python
import os
from fastapi import UploadFile

# 上传文件保存目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/upload")
async def upload_file(file: UploadFile):
    # 保存文件到本地
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    content = await file.read()

    with open(file_path, 'wb') as f:
        f.write(content)

    return {"success": True, "filename": file.filename}
```

### 使用注意

- 文件保存在后端的 `uploads/` 文件夹
- 无需数据库记录（如果需要可自行添加）
- 生产环境可考虑限制文件大小和类型

## Docker部署

> **需要完整的 Docker 构建、推送阿里云 ACR、服务器部署流程？**
> 请使用 `docker-acr-deploy` 技能获取详细指南。

### 最简检查清单

- [ ] 前端 `dist/` 目录已生成
- [ ] `requirements.txt` 包含 `fastapi`
- [ ] Dockerfile 中 WORKDIR 是 `/app`
- [ ] 本地容器测试通过后再部署

## 常见问题

**Q: 什么时候该用Vue/React而不是原生JS？**
A: 页面有复杂交互（如表单验证、动态列表、数据绑定）再用Vue/React。简单展示页面用原生JS即可。

**Q: 什么时候该换MySQL/PostgreSQL？**
A: 需要多用户同时访问、有复杂查询需求、或数据量超过1万条时再考虑。

**Q: 前端怎么连接后端API？**
A: 使用fetch或axios发起HTTP请求，后端需要配置CORS允许跨域访问。

## 沙箱中打开应用

**重要：** 只要有程序启动的URL地址，必须执行以下操作：

1. 让沙箱浏览器重定向到该URL
2. 向用户返回链接：`http://{沙箱VNC地址}/vnc/index.html?autoconnect=true`，方便用户直接在新窗口打开

