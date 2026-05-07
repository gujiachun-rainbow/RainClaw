---
name: docker-build-push
description: Podman 镜像构建与推送。包含 Dockerfile 编写、本地构建测试、推送到阿里云 ACR 个人版仓库。当用户需要制作 Dockerfile、打包镜像、推送镜像时使用此技能。
---

# Podman 构建与推送

## 0. 前提条件

### 检查 Podman 是否已安装

**Windows（PowerShell）：**
```powershell
podman --version
# 输出示例：podman version 4.9.0
```

**macOS/Linux（终端）：**
```bash
podman --version
# 输出示例：podman version 4.9.0
```

如果命令返回版本信息，说明已安装；如果提示 `podman : 无法将“podman”项识别为 cmdlet` 或 `command not found`，则需要安装。

### 安装 Podman

**Windows 系统：**
```powershell
winget install RedHat.Podman
```

**macOS 系统：**
```bash
brew install podman
```

**Linux 系统（以 CentOS/RHEL 为例）：**
```bash
sudo dnf install podman
```

> ⚠️ Podman 安装完成后，需要重启终端或重新登录会话使环境变量生效。

## 1. 推荐基础镜像

| 类型 | 推荐镜像 |
|------|----------|
| Python | `crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/python:3.12.13-slim-trixie` |
| Node.js | `crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/node:22.22.2-trixie-slim` |
| Nginx | `crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/nginx:stable-alpine` |

## 2. Dockerfile 模板（前后端合一）

一个镜像、一个容器、一个命令，前后端打包在一起。

```dockerfile
FROM crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com/rainclaw/python:3.12.13-slim-trixie

# 避免中文输出乱码
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# 先装依赖（利用缓存层）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端文件（原生HTML或打包后的dist）
COPY frontend/dist/ ./dist/

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### requirements.txt

```
fastapi
uvicorn
python-multipart
pandas
openpyxl
```

> 根据实际项目删减，`pandas`/`openpyxl` 仅 Excel 导入时需要。

## 3. 前端打包

**方式A：原生 HTML/CSS/JS（无框架）**
- 直接放到 `frontend/` 目录，Dockerfile 里 `COPY frontend/ ./frontend/`
- 后端用 `FileResponse` 按上述方式逐个返回

**方式B：Vue/React（Vite 打包）**
```bash
cd frontend && npm install && npm run build
# 生成 frontend/dist/
```
- Dockerfile 里 `COPY frontend/dist/ ./dist/`

## 4. 构建与本地测试

```powershell
# 构建镜像
podman build -t myapp:latest .

# 本地运行测试
podman run -d --name myapp -p 8000:8000 myapp:latest

# 查看日志（确认启动无报错）
podman logs myapp

# 测试 API
curl.exe http://localhost:8000/api/products

# 清理
podman rm -f myapp
```

## 5. 推送到阿里云 ACR

### 5.1 前置：在 ACR 控制台创建仓库

1. 打开 ACR 控制台，找到实例地址（如 `crpi-xxxxxx.cn-shanghai.personal.cr.aliyuncs.com`）
2. **命名空间管理** → 创建命名空间（如 `web-soft`）
3. **仓库列表** → **创建仓库** → 填写命名空间 + 仓库名（如 `ecommerce-admin`）

> ⚠️ 仓库**不会自动创建**，推送前必须先在控制台建好，否则报 `insufficient_scope`。

### 5.2 登录

阿里云 ACR 登录密码**不是阿里云账号密码**，是在 ACR 控制台设置的独立访问密码。

```powershell
podman login --username=<用户名> --password=<密码> <ACR实例地址>
```

> ⚠️ PowerShell 中 `--password-stdin` + `echo "xxx" |` 不生效，直接用 `--password=` 参数最简单。

### 5.3 打标签 + 推送

```powershell
# 打标签（默认推荐 latest）
podman tag myapp:latest <ACR实例地址>/<命名空间>/<仓库名>:latest

# 推送
podman push <ACR实例地址>/<命名空间>/<仓库名>:latest
```

> 💡 生产环境推荐使用语义化版本（如 `v1.0.0`）替代 `latest`，便于回滚。

### 5.4 已知的 ACR 地址

```
ACR实例地址: crpi-st7s4gabmi4ym1qo.cn-shanghai.personal.cr.aliyuncs.com
命名空间: web-soft
```

## 6. ⚠️ 常见错误

### 错误 1：模块导入路径 `ModuleNotFoundError`

**症状：**
```
ModuleNotFoundError: No module named 'database'
```

**修复：** 请参考 `simple-web-dev-guide` 技能中的"模块导入路径"规范，使用 `from backend.xxx import` 格式。

### 错误 2：`insufficient_scope: authorization failed`

仓库不存在。去 ACR 控制台创建命名空间 + 仓库后再推送。

### 错误 3：`unauthorized: authentication required`

用户名或密码错误。ACR 密码是独立访问密码，不是阿里云账号密码。

### 错误 4：PowerShell `&&` 报错

PowerShell 5.x 不支持 `&&`。用 pwsh（PowerShell 7+）或分步执行。

### 错误 5：PowerShell 中文乱码

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```
或用 Python 脚本处理，避免直接在终端输出中文。

### 错误 6：`No such image`

`podman images` 确认本地镜像名，用引号包裹含特殊字符的完整路径。

## 7. 构建与推送检查清单

- [ ] Podman 已安装并验证（`podman --version`）
- [ ] Dockerfile 中 `WORKDIR /app`（不是 `/app/backend`）
- [ ] `CMD` 用 `uvicorn backend.main:app`（模块路径格式）
- [ ] `main.py` 所有 `from xxx import` 已改为 `from backend.xxx import`
- [ ] 本地 `podman build` 成功
- [ ] 本地 `podman run` + `podman logs` 确认启动无报错
- [ ] `curl.exe localhost:8000` API 返回正常
- [ ] ACR 控制台已创建命名空间和仓库
- [ ] `podman login` 成功
- [ ] `podman push` 成功
