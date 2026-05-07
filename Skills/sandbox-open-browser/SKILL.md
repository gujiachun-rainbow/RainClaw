---
name: sandbox-open-browser
description: "当沙箱中有 Web 应用启动并有 URL 地址时自动打开沙箱浏览器。触发场景：检测到 Python Web 服务启动（uvicorn/fastapi/flask/streamlit/gradio/http.server 等）并生成了 URL；用户说'打开浏览器'/'访问这个地址'/'打开网页看看'/'打开链接'/'打开 VNC'等；需要让用户通过 VNC 查看 Web 界面时。核心动作：探测服务端口就绪 → 启动沙箱 chromium 浏览器 → 返回 VNC 访问链接给用户。"
---

# Sandbox Open Browser — 在沙箱中打开 Web 应用

在沙箱开发环境中，当 Web 应用启动后，自动完成：**探测服务端口就绪 → 启动沙箱 chromium 浏览器 → 返回 VNC 访问链接**。

## 环境信息

- **沙箱 VNC 地址**: `{沙箱VNC地址}`（从记忆读取，格式如 `localhost:8080`）
- **显示器**: `DISPLAY=:99`
- **浏览器**: `/usr/bin/chromium-browser`
- **VNC 访问链接格式**: `http://{沙箱VNC地址}/vnc/index.html?autoconnect=true`

## 工作流程

### 0. 前置清理（可选）

如果之前已经打开过浏览器实例，建议先清理旧进程，避免窗口堆积：

```bash
pkill -f "chromium" 2>/dev/null
sleep 1
```

### 1. 获取并清理 URL

从上下文或用户输入中获取 Web 应用的完整 URL，并做标准化处理。

**URL 来源**：
- 开发服务器启动时通常会输出类似 `Uvicorn running on http://0.0.0.0:8000` 的信息
- 用户可能直接说"打开 http://localhost:3000"
- 用户可能提到端口号，需要拼接成完整 URL

**URL 标准化**：
- 如果 URL 中使用了 `0.0.0.0`，必须替换为 `localhost`，因为浏览器无法解析 `0.0.0.0`
- 确保有 `http://` 前缀，如果没有则补上

```bash
URL=$(echo "$URL" | sed 's/0\.0\.0\.0/localhost/g')
URL=$(echo "$URL" | sed 's|^https\?://||; s|^|http://|')
```

### 2. 探测服务是否就绪（必须）

**在打开浏览器之前，必须先确认服务已启动并可以响应请求。** 使用 `curl` 循环探测：

```bash
echo "正在探测服务就绪状态..."
SERVICE_READY=false
for i in $(seq 1 30); do
  if curl -sf --connect-timeout 2 "$URL" > /dev/null 2>&1; then
    echo "✅ 服务已就绪 ($i/30)"
    SERVICE_READY=true
    break
  fi
  echo "等待服务就绪... ($i/30)"
  sleep 1
done

if [ "$SERVICE_READY" = false ]; then
  echo "⚠️ 30 秒后服务仍未就绪，仍尝试打开浏览器"
fi
```

- **最多等待 30 秒**
- **每 1 秒探测一次**
- 如果 30 秒后仍未就绪，打印警告但仍尝试打开浏览器（可能是非 HTTP 的 WebSocket 服务等）

### 3. 启动沙箱浏览器

使用 `chromium-browser` 以无沙箱模式打开 URL，确保在当前 DISPLAY 中渲染：

```bash
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu "$URL" &
```

**参数说明**：
- `--no-sandbox`：沙箱内运行必须（外层已经是容器隔离）
- `--disable-gpu`：无 GPU 环境下避免错误日志
- `&`：后台运行，不阻塞后续操作

### 4. 返回 VNC 访问链接给用户

**重要：向用户返回以下格式的链接，方便直接在新窗口打开：**

```
http://{沙箱VNC地址}/vnc/index.html?autoconnect=true
```

推荐格式：
> ✅ 已通过沙箱浏览器打开 `http://localhost:8000`
> VNC 查看：http://{沙箱VNC地址}/vnc/index.html?autoconnect=true

**必须同时做两件事**：
1. 通过 `execute` 命令调用 `chromium-browser` 在沙箱中打开 URL
2. 在回复中明确返回 VNC 链接给用户

### 5. 窗口最大化（推荐）

浏览器启动后，最大化窗口以获得更好的 VNC 查看体验：

```bash
sleep 2
WINDOW_ID=$(xdotool search --onlyvisible --class "chromium" 2>/dev/null | tail -1)
if [ -n "$WINDOW_ID" ]; then
  xdotool windowactivate "$WINDOW_ID" --sync
  xdotool key --window "$WINDOW_ID" "F11"
fi
```

## 完整示例

### 示例 1：用户启动 FastAPI 应用后

```text
用户：我启动了 FastAPI 应用在 http://localhost:8000
你（Agent）的处理流程：

# 1. 清理旧进程
pkill -f "chromium" 2>/dev/null
sleep 1

# 2. 探测服务
URL="http://localhost:8000"
echo "正在探测 $URL..."
for i in $(seq 1 30); do
  if curl -sf "$URL" > /dev/null 2>&1; then
    echo "✅ 服务已就绪"
    break
  fi
  echo "等待... ($i/30)"
  sleep 1
done

# 3. 打开浏览器
DISPLAY=:99 chromium-browser --no-sandbox --disable-gpu "$URL" &

# 4. 最大化窗口
sleep 2
WID=$(xdotool search --onlyvisible --class "chromium" 2>/dev/null | tail -1)
[ -n "$WID" ] && xdotool windowactivate "$WID" --sync && xdotool key --window "$WID" "F11"

# 5. 输出给用户
echo "✅ 已打开沙箱浏览器"
echo "VNC 查看: http://{沙箱VNC地址}/vnc/index.html?autoconnect=true"
```

### 示例 2：用户给出 0.0.0.0 地址

```text
用户：帮我打开 http://0.0.0.0:7860
你：先标准化 URL → http://localhost:7860 → 然后按上述流程执行
```

## 注意事项

1. **必须探测服务就绪**：不要假设服务已启动就立即打开浏览器，否则浏览器会显示"无法访问此网站"
2. **URL 转换**：`0.0.0.0` 必须替换为 `localhost`（浏览器不支持 `0.0.0.0`）
3. **端口验证**：如果浏览器打开后页面空白，用 `ss -tlnp | grep <端口>` 确认服务是否在运行
4. **多标签页**：连续多次调用此技能会在同一 Chromium 实例中打开新标签页，这是正常行为
5. **DISPLAY 变量**：每次调用 `chromium-browser` 时必须显式指定 `DISPLAY=:99`，否则浏览器无法在沙箱显示中渲染
6. **xdotool 窗口 ID**：多次打开后可能有多个 chromium 窗口，用 `tail -1` 取最新的
