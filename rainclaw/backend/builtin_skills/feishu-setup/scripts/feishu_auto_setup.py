#!/usr/bin/env python3
"""Feishu Open Platform auto-setup via sandbox browser MCP (JSON-RPC 2.0).
Usage: python3 feishu_auto_setup.py <command> [--name NAME]
Commands: open_login | check_login | create_app | add_bot | get_credentials
          configure_events | configure_permissions | publish_app
"""
import argparse, json, os, re, sys, time
import httpx

MCP = "http://localhost:8080/mcp"
FEISHU_URL = "https://open.feishu.cn/app?lang=zh-CN"
_id = 0

_MCP_HEADERS = {"Accept": "application/json, text/event-stream"}

def call(tool, args={}):
    global _id; _id += 1
    try:
        r = httpx.post(MCP, json={"jsonrpc":"2.0","id":_id,"method":"tools/call",
            "params":{"name":tool,"arguments":args}},
            headers=_MCP_HEADERS, timeout=30)
        raw = r.json()
        result = raw.get("result", {})
        content = result.get("content", [])
        return "\n".join(c.get("text","") for c in content if c.get("type")=="text")
    except Exception:
        return ""

def call_raw(tool, args={}):
    global _id; _id += 1
    try:
        r = httpx.post(MCP, json={"jsonrpc":"2.0","id":_id,"method":"tools/call",
            "params":{"name":tool,"arguments":args}},
            headers=_MCP_HEADERS, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def list_tools():
    global _id; _id += 1
    try:
        r = httpx.post(MCP, json={"jsonrpc":"2.0","id":_id,"method":"tools/list","params":{}},
            headers=_MCP_HEADERS, timeout=30)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def nav(url): return call("browser_navigate", {"url": url})
def snap():
    elems = call("browser_get_clickable_elements")
    text = call("browser_get_text")
    return elems + "\n---PAGE_TEXT---\n" + text
def click(idx): return call("browser_click", {"index": int(idx)})
def fill(idx, v): return call("browser_form_input_fill", {"index": int(idx), "value": v, "clear": True})
def fill_selector(sel, v): return call("browser_form_input_fill", {"selector": sel, "value": v, "clear": True})
def browser_eval(script): return call("browser_evaluate", {"script": script})
def browser_eval_raw(script): return call_raw("browser_evaluate", {"script": script})
def vision_click(x, y): return call("browser_vision_screen_click", {"x": x, "y": y})
def press_key(key): return call("browser_press_key", {"key": key})
def wait(s=3): time.sleep(s); return snap()

_ELEM_RE = re.compile(r"^\[(\d+)\]<([^>]*)>(.*?)(?:</[^>]*>)?$")
_INPUT_TAGS = re.compile(r"^(input|textbox|textarea)", re.IGNORECASE)

def find(text, s):
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if m and text in m.group(3):
            return m.group(1)
    if "---PAGE_TEXT---" in s:
        page_text = s.split("---PAGE_TEXT---", 1)[1]
        if text in page_text:
            for line in s.split("---PAGE_TEXT---", 1)[0].splitlines():
                m = _ELEM_RE.match(line.strip())
                if m and text in line:
                    return m.group(1)
    return None

def find_input_after(label_text, s):
    """Find the first input/textbox/textarea element after a label containing label_text."""
    found_label = False
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        tag = m.group(2).split()[0] if m.group(2) else ""
        if not found_label:
            if label_text in m.group(3) or label_text in line:
                found_label = True
                if _INPUT_TAGS.match(tag):
                    return m.group(1)
            continue
        if _INPUT_TAGS.match(tag):
            return m.group(1)
    return None

def find_first_input(s):
    """Find the first input/textbox/textarea in the clickable elements (e.g. modal search box with no label)."""
    part = s.split("---PAGE_TEXT---", 1)[0]
    for line in part.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        tag = (m.group(2) or "").split()[0]
        if _INPUT_TAGS.match(tag):
            return m.group(1)
    return None

_ICON_TAGS = re.compile(r"^(button|span|svg|a|img|icon)", re.IGNORECASE)

def find_icon_after(label_text, s):
    """Find the first small clickable element (button/span/svg/icon) right after a label."""
    found_label = False
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        tag = m.group(2).split()[0] if m.group(2) else ""
        elem_text = m.group(3).strip()
        if not found_label:
            if label_text in elem_text or label_text in line:
                found_label = True
            continue
        if _ICON_TAGS.match(tag) and len(elem_text) <= 4:
            return m.group(1)
    return None

def find_exact_button(text, s):
    """Find a button/link whose text matches exactly (not substring of a longer text)."""
    candidates = []
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        elem_text = m.group(3).strip()
        if elem_text == text:
            candidates.append(m.group(1))
    return candidates[-1] if candidates else None


def find_exact_button_by_tag(text, s, tag_want="button"):
    """Find clickable element with exact text and given tag (e.g. button), to avoid clicking links that open new page."""
    for line in s.split("---PAGE_TEXT---", 1)[0].splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        tag = (m.group(2) or "").split()[0].lower()
        elem_text = (m.group(3) or "").strip()
        if elem_text == text and tag == tag_want.lower():
            return m.group(1)
    return None


def find_checkbox_or_ref_for_event(s, *labels):
    """在事件列表中优先点该行的 checkbox，避免点到事件名链接（会打开新页）。若同行前一个元素是 input/checkbox 或短文案的 span/div 则返回其 ref，否则返回匹配文案的 ref。"""
    part = s.split("---PAGE_TEXT---", 1)[0]
    lines = part.splitlines()
    ref_tag_text = []
    for line in lines:
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        ref_tag_text.append((m.group(1), (m.group(2) or "").split()[0].lower(), m.group(3) or ""))
    for i, (ref, tag, text) in enumerate(ref_tag_text):
        if not any(lbl in text for lbl in labels):
            continue
        if i > 0:
            prev_ref, prev_tag, prev_text = ref_tag_text[i - 1]
            prev_short = len((prev_text or "").strip()) <= 2
            if prev_tag == "input" or "checkbox" in prev_tag or "check" in prev_tag or (prev_tag in ("span", "div") and prev_short):
                return prev_ref
        return ref
    return None


def find_checkbox_or_ref_for_permission(s, *labels):
    """在权限列表中优先点该行的 checkbox。权限 UI 中 checkbox 可能在名称前或后，故同时检查前、后相邻元素。"""
    part = s.split("---PAGE_TEXT---", 1)[0]
    lines = part.splitlines()
    ref_tag_text = []
    for line in lines:
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        ref_tag_text.append((m.group(1), (m.group(2) or "").split()[0].lower(), (m.group(3) or "").strip()))
    for i, (ref, tag, text) in enumerate(ref_tag_text):
        if not any(lbl in text for lbl in labels):
            continue
        def is_checkbox_like(t, txt):
            if t == "input" or "checkbox" in t or "check" in t:
                return True
            if t in ("span", "div") and len((txt or "").strip()) <= 2:
                return True
            return False
        if i > 0 and is_checkbox_like(ref_tag_text[i - 1][1], ref_tag_text[i - 1][2]):
            return ref_tag_text[i - 1][0]
        for j in (1, 2):
            if i + j < len(ref_tag_text):
                nr, nt, ntxt = ref_tag_text[i + j]
                if is_checkbox_like(nt, ntxt):
                    return nr
        if i > 0:
            return ref_tag_text[i - 1][0]
        return ref
    return None


def click_permission_checkbox_by_js(permission_name):
    """在页面中查找包含权限名的行，若该行 checkbox 未勾选则点击。返回 'clicked' | 'already_checked' | 'not_found'。"""
    text_escaped = json.dumps(permission_name, ensure_ascii=False)
    script = (
        "(function(){"
        "var text = " + text_escaped + ";"
        "var all = document.querySelectorAll('tr, [role=row], [class*=\"row\"], [class*=\"item\"]');"
        "for (var i = 0; i < all.length; i++) {"
        "  var row = all[i];"
        "  if (row.textContent && row.textContent.indexOf(text) >= 0) {"
        "    var cb = row.querySelector('input[type=checkbox]');"
        "    if (cb) { if (cb.checked) return 'already_checked'; cb.click(); return 'clicked'; }"
        "  }"
        "}"
        "var any = document.querySelectorAll('*');"
        "for (var j = 0; j < any.length; j++) {"
        "  var el = any[j];"
        "  if (el.children.length === 0 && el.textContent && el.textContent.trim().indexOf(text) >= 0) {"
        "    var r = el.closest('tr') || el.closest('[role=row]');"
        "    if (r) { var c = r.querySelector('input[type=checkbox]'); if (c) { if (c.checked) return 'already_checked'; c.click(); return 'clicked'; } }"
        "  }"
        "}"
        "return 'not_found';"
        "})()"
    )
    try:
        out = (browser_eval(script) or "").strip()
        if "already_checked" in out:
            return "already_checked"
        if "clicked" in out:
            return "clicked"
        return "not_found"
    except Exception:
        return "not_found"


def is_permission_checked_by_js(permission_name):
    """检查该权限行的 checkbox 是否已勾选。用于 ref 点击前判断，避免重复点击导致取消勾选。"""
    text_escaped = json.dumps(permission_name, ensure_ascii=False)
    script = (
        "(function(){"
        "var text = " + text_escaped + ";"
        "var all = document.querySelectorAll('tr, [role=row], [class*=\"row\"], [class*=\"item\"]');"
        "for (var i = 0; i < all.length; i++) {"
        "  var row = all[i];"
        "  if (row.textContent && row.textContent.indexOf(text) >= 0) {"
        "    var cb = row.querySelector('input[type=checkbox]');"
        "    if (cb) return cb.checked ? 'yes' : 'no';"
        "  }"
        "}"
        "return 'no';"
        "})()"
    )
    try:
        out = (browser_eval(script) or "").strip()
        return "yes" in out
    except Exception:
        return False


def find_all_refs(text, s):
    """Find all clickable element indices whose text contains `text`. Used to open existing app by name (first if duplicates)."""
    refs = []
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        elem_text = (m.group(3) or "").strip()
        # 匹配元素文本或整行（避免内容被截断或名字在标签属性里）
        if text in elem_text or text in line:
            refs.append(m.group(1))
    if not refs and "---PAGE_TEXT---" in s:
        page_text = s.split("---PAGE_TEXT---", 1)[1]
        if text in page_text:
            for line in s.split("---PAGE_TEXT---", 1)[0].splitlines():
                m = _ELEM_RE.match(line.strip())
                if m and text in line:
                    refs.append(m.group(1))
    return refs


def find_refs_exact(text, s):
    """Find all clickable element indices whose text equals `text` exactly (after strip). 用于按名称完全匹配打开应用。"""
    refs = []
    part = s.split("---PAGE_TEXT---", 1)[0]
    for line in part.splitlines():
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        elem_text = (m.group(3) or "").strip()
        if elem_text == text:
            refs.append(m.group(1))
    return refs


def _refs_with_tag(refs, s, tags):
    """从快照 s 中筛选出 tag 在 tags 内的 ref 列表，保持顺序。"""
    tag_by_ref = {}
    for line in s.splitlines():
        m = _ELEM_RE.match(line.strip())
        if m:
            tag = (m.group(2) or "").split()[0].lower()
            tag_by_ref[m.group(1)] = tag
    return [r for r in refs if tag_by_ref.get(r, "").lower() in tags]


def find_editor_by_json_content(s):
    """在批量导入权限弹窗中，通过默认 JSON 内容（scopes/tenant）定位编辑器元素。
    日志证实：JSON 在 [2]<div>... 内，内容含换行。
    不能用“从任意 [idx] 到后续 scopes/tenant”的宽松匹配，否则会错误命中 [0]。"""
    part = s.split("---PAGE_TEXT---", 1)[0]
    m = re.search(
        r"\[(\d+)\]<div>批量导入/导出权限[\s\S]*?\"scopes\"[\s\S]*?\"tenant\"[\s\S]*?</div>",
        part,
    )
    return m.group(1) if m else None


def find_secret_eye_after_label(s, anchor_text="App Secret"):
    """在 App Secret 后、下一个 label 前，选择第 2 个 span。

    运行时证据表明 MCP 返回的候选顺序为：
    div 包装层 -> span(复制) -> span(眼睛) -> button(刷新)
    因此应忽略包装层，命中第 2 个 span。
    """
    lines = s.split("---PAGE_TEXT---", 1)[0].splitlines()
    found_anchor = False
    span_refs = []
    for line in lines:
        m = _ELEM_RE.match(line.strip())
        if not m:
            continue
        tag = (m.group(2) or "").split()[0]
        if not found_anchor:
            if anchor_text in line or anchor_text in m.group(3):
                found_anchor = True
            continue
        if tag == "label":
            break
        if tag == "span":
            span_refs.append(m.group(1))
            if len(span_refs) == 2:
                return m.group(1)
    return None

def click_text(text, s, w=3):
    ref = find(text, s)
    if ref: click(ref); return wait(w)
    return s

def out(d): print(json.dumps(d, ensure_ascii=False))

# ── commands ──────────────────────────────────────────────────────

def _is_logged_in(s):
    return any(k in s for k in ("我的应用", "创建企业自建应用", "My Apps", "Create Custom App"))

def _is_landing_page(s):
    return any(k in s for k in ("Developer Console", "开发者后台", "Customer Stories"))

def open_login():
    nav(FEISHU_URL)
    s = wait(5)
    if _is_landing_page(s) and not _is_logged_in(s):
        ref = find("Developer Console", s) or find("开发者后台", s)
        if ref:
            click(ref)
            s = wait(5)
    status = "already_logged_in" if _is_logged_in(s) else "waiting_for_login"
    out({"status": status, "message": "请在浏览器面板扫码登录飞书" if status == "waiting_for_login" else "已登录"})

def check_login():
    s = snap()
    if _is_logged_in(s):
        out({"status": "logged_in"}); return
    nav(FEISHU_URL); s = wait(5)
    out({"status": "logged_in" if _is_logged_in(s) else "not_logged_in"})

def create_app(name):
    nav(FEISHU_URL); s = wait(3)
    # 若应用名称已存在则直接打开；有重名则打开第一个
    if _is_logged_in(s):
        # 先进入「我的应用」列表，确保应用卡片在视口内
        list_ref = find("我的应用", s) or find("My Apps", s)
        if list_ref:
            click(list_ref); s = wait(2)
        s = snap()
        existing_refs = find_refs_exact(name, s)
        if existing_refs:
            # 优先点击链接/卡片类元素（a、link、div、button），避免点到纯文案
            preferred = _refs_with_tag(existing_refs, s, ["a", "link", "div", "button"])
            ref_to_click = preferred[0] if preferred else existing_refs[0]
            click(ref_to_click)
            s = wait(3)
            # 确认已进入应用详情（有凭证/应用能力等）
            if any(k in s for k in ("凭证与基础信息", "凭证", "App ID", "应用能力", "版本管理")):
                out({"status": "opened", "app_name": name})
                return

    s = click_text("创建企业自建应用", s) or click_text("创建应用", s)
    s = wait(2)

    name_ref = find_input_after("应用名称", s)
    if name_ref:
        fill(name_ref, name); time.sleep(0.5); s = wait(1)

    desc_ref = find_input_after("应用描述", s)
    if desc_ref:
        fill(desc_ref, name); time.sleep(0.5); s = wait(1)

    create_btn = find_exact_button("创建", s)
    if create_btn:
        click(create_btn); s = wait(3)
    else:
        s = click_text("确认创建", s) or click_text("创建", s) or click_text("确定", s)
        s = wait(3)

    out({"status": "created", "app_name": name})

def add_bot():
    s = snap()
    s = click_text("添加应用能力", s) or click_text("应用能力", s); s = wait(2)
    s = click_text("机器人", s); s = wait(2)
    ref = find("配置", s)
    if ref:
        click_text('取消', s); s = wait(2)
        out({"status": "bot_already_added"})
        return
    ref = find("添加", s)
    if not ref:
        ref = find("配置", s)
    if ref: click(ref); s = wait(2)

    out({"status": "bot_added"})

_APP_ID_RE = re.compile(r"cli_[a-f0-9]{16,}")
_APP_SECRET_RE = re.compile(r"(?<![*])[A-Za-z0-9_]{28,}(?![*])")

def get_credentials():
    s = snap()
    s = click_text("凭证与基础信息", s) or click_text("凭证", s); s = wait(3)

    app_id = None
    m = _APP_ID_RE.search(s)
    if m:
        app_id = m.group(0)

    ref = find_secret_eye_after_label(s, "App Secret")

    if not ref:
        out({"status": "error", "message": "未找到显示 App Secret 的按钮"})
        return

    click(ref); s = wait(2)

    s = snap()
    page_text = s.split("---PAGE_TEXT---", 1)[1] if "---PAGE_TEXT---" in s else s
    secret_pos = page_text.find("App Secret")

    app_secret = None
    if secret_pos >= 0:
        after_secret = page_text[secret_pos:]
        m = _APP_SECRET_RE.search(after_secret)
        if m and not m.group(0).startswith("cli_"):
            app_secret = m.group(0)

    result = {"status": "ok"}
    if app_id: result["app_id"] = app_id
    else: result["app_id_error"] = "请手动从页面复制 App ID"
    if app_secret: result["app_secret"] = app_secret
    else: result["app_secret_error"] = "请手动从页面复制 App Secret"
    out(result)

def configure_events():
    s = snap()
    s = click_text("事件与回调", s) or click_text("事件", s); s = wait(3)
    s = click_text("事件配置", s); s = wait(2)
    edit_ref = find_icon_after("订阅方式", s)
    if edit_ref:
        click(edit_ref); s = wait(2)
    s = click_text("使用长连接接收事件", s) or click_text("长连接", s); s = wait(2)
    ref = find("保存", s)
    if ref: click(ref); s = wait(2)

    s = snap()
    s = click_text("回调配置", s); s = wait(2)
    edit_ref = find_icon_after("订阅方式", s)
    if edit_ref:
        click(edit_ref); s = wait(2)
    s = click_text("使用长连接接收回调", s) or click_text("长连接", s); s = wait(2)
    ref = find("保存", s)
    if ref: click(ref); s = wait(2)

    # 回调配置：添加回调「卡片回传交互」card.action.trigger
    s = snap()
    s = click_text("回调配置", s); s = wait(2)
    add_cb_ref = find_exact_button_by_tag("添加回调", s, "button") or find_exact_button("添加回调", s) or find("添加回调", s)
    if add_cb_ref:
        click(add_cb_ref); s = wait(2)
        s = snap()
        card_tab = find("卡片", s)
        if card_tab:
            click(card_tab); s = wait(1)
            s = snap()
        search_ref = find_input_after("搜索", s) or find_first_input(s)
        if search_ref:
            fill(search_ref, "卡片回传"); s = wait(1)
        s = snap()
        result = click_permission_checkbox_by_js("卡片回传交互")
        if result not in ("clicked", "already_checked"):
            r = find_checkbox_or_ref_for_event(s, "卡片回传交互", "card.action.trigger") or find("卡片回传交互", s) or find("card.action.trigger", s)
            if r:
                click(r); s = wait(0.3)
                s = snap()
        else:
            s = wait(0.5)
        confirm_ref = find_exact_button("添加", s) or find_exact_button("确认添加", s) or find_exact_button_by_tag("确认添加", s, "button") or find("确认添加", s) or find("确认", s)
        if confirm_ref:
            click(confirm_ref); s = wait(2)
        else:
            press_key("Enter"); s = wait(2)

    # 分两次添加事件（滚动在弹窗内不生效）：第一次添加两个 reaction，第二次再打开弹窗只添加「接收消息」
    s = snap()
    s = click_text("事件配置", s); s = wait(2)
    # 只点 button 上的「添加事件」，避免点到侧栏等处的链接（会跳转外链）
    add_evt_ref = find_exact_button_by_tag("添加事件", s, "button") or find_exact_button("添加事件", s) or find("添加事件", s)
    if add_evt_ref:
        click(add_evt_ref); s = wait(2)
        s = snap()
        msg_cat_ref = find("消息与群组", s)
        if msg_cat_ref:
            click(msg_cat_ref); s = wait(1)
            s = snap()
        search_ref = find_input_after("搜索", s) or find_input_after("Q", s) or find_first_input(s)
        if search_ref:
            fill(search_ref, "消息"); s = wait(1)
        s = snap()
        # 第一次：只勾选 消息被reaction、消息被取消reaction（优先点 checkbox 避免点到链接打开新页）
        for primary, fallback, api_id in [
            ("消息被reaction v2.0", "消息被reaction", "im.message.reaction.created_v1"),
            ("消息被取消reaction v2.0", "消息被取消reaction", "im.message.reaction.deleted_v1"),
        ]:
            r = find_checkbox_or_ref_for_event(s, primary, fallback, api_id) or find(primary, s) or find(fallback, s) or find(api_id, s)
            if r:
                click(r); s = wait(0.3)
                s = snap()
        # confirm_ref = find_exact_button("添加", s) or find_exact_button_by_tag("确认添加", s, "button") or find("确认添加", s) or find("确认", s)
        # if confirm_ref:
        #     click(confirm_ref); s = wait(2)
        # else:
        #     press_key("Enter"); s = wait(2)

        # 第二次：再点「添加事件」，只勾选「接收消息」后确认添加
        # s = snap()
        # s = click_text("事件配置", s); s = wait(2)
        # add_evt_ref2 = find_exact_button_by_tag("添加事件", s, "button") or find_exact_button("添加事件", s) or find("添加事件", s)
        # if add_evt_ref2:
        #     click(add_evt_ref2); s = wait(2)
        #     s = snap()
        #     msg_cat_ref2 = find("消息与群组", s)
        #     if msg_cat_ref2:
        #         click(msg_cat_ref2); s = wait(1)
        #         s = snap()
        search_ref2 = find_input_after("搜索", s) or find_input_after("Q", s) or find_first_input(s)
        if search_ref2:
            fill(search_ref2, "接收消息"); s = wait(1)
        s = snap()
        # 优先点「接收消息」行的 checkbox，避免点到事件名链接（会打开新页）
        r = find_checkbox_or_ref_for_event(s, "接收消息 v2.0", "接收消息", "im.message.receive_v1") or find("接收消息 v2.0", s) or find("接收消息", s) or find("im.message.receive_v1", s)
        if r:
            click(r); s = wait(0.3)
            s = snap()
        confirm_ref2 = find_exact_button("添加", s) or find_exact_button("确认开通", s) or find_exact_button_by_tag("确认开通", s, "button") or find("确认添加", s) or find("确认", s)
        if confirm_ref2:
            click(confirm_ref2); s = wait(2)
        else:
            press_key("Enter"); s = wait(2)

    out({"status": "events_configured"})

def configure_permissions(app_name="ScienceClaw 助手", scope="all"):
    try:
        _configure_permissions_impl(app_name, scope)
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        out({"status": "error", "command": "configure_permissions", "message": str(e)})
        sys.exit(1)


def _configure_permissions_impl(app_name, scope="all"):
    nav(FEISHU_URL); s = wait(3)
    click_text("我的应用", s); s = wait(2)
    s = snap()
    existing_refs = find_refs_exact(app_name, s)
    if existing_refs:
        preferred = _refs_with_tag(existing_refs, s, ["a", "link", "div", "button"])
        ref_to_click = preferred[0] if preferred else existing_refs[0]
        click(ref_to_click); s = wait(3)
    s = snap()
    click_text("权限管理", s); s = wait(2)
    s = snap()
    # 参考「添加事件」流程：先通过「开通权限」勾选权限
    enable_perm_ref = find_exact_button_by_tag("开通权限", s, "button") or find_exact_button("开通权限", s) or find("开通权限", s)
    if enable_perm_ref:
        click(enable_perm_ref); s = wait(2)
        s = snap()
        if scope in ("app", "all"):
            # 先点击「应用身份权限 tenant_access_token」确保在该 Tab 下
            tenant_tab = find("应用身份权限", s) or find("tenant_access_token", s)
            if tenant_tab:
                click(tenant_tab); s = wait(1)
                s = snap()
            # 应用身份权限 tenant_access_token
            search_ref = find_input_after("搜索", s) or find_input_after("例如", s) or find_first_input(s)
            PERM_LIST = [
                ("获取卡片信息", "cardkit:card:read"),
                ("创建与更新卡片", "cardkit:card:write"),
                ("获取单聊、群组消息", "im:message:readonly"),
                ("撤回消息", "im:message:recall"),
                ("以应用的身份发消息", "im:message:send_as_bot"),
                ("给多个用户批量发消息", "im:message:send_multi_users"),
                ("发送特定模板系统消息", "im:message:send_sys_msg"),
                ("更新消息", "im:message:update"),
                ("接收群聊中@机器人消息事件", "im:message.group_at_msg:readonly"),
                ("读取用户发给机器人的单聊消息", "im:message.p2p_msg:readonly"),
                ("查看 Pin 消息", "im:message.pins:read"),
                # ("添加、取消 Pin 消息", "im:message.pins:write_only"),
                ("查看消息表情回复", "im:message.reactions:read"),
                ("发送、删除消息表情回复", "im:message.reactions:write_only"),
                ("获取与上传图片或文件资源", "im:resource"),
                ("查看群信息", "im:chat:read"),
                ("更新群信息", "im:chat:update"),
                ("获取卡片模板信息", "cardkit:template:read"),
                ("获取通讯录基本信息", "contact:contact.base:readonly"),
                ("查看新版文档", "docx:document:readonly"),
            ]
            for name, perm_scope in PERM_LIST:
                search_ref = find_input_after("搜索", s) or find_input_after("例如", s) or find_first_input(s)
                if search_ref:
                    fill(search_ref, name); s = wait(1.5)
                s = snap()
                result = click_permission_checkbox_by_js(name)
                if result == "already_checked":
                    continue
                if result == "clicked":
                    s = wait(0.8)
                else:
                    if is_permission_checked_by_js(name):
                        continue
                    r = find_checkbox_or_ref_for_permission(s, name, perm_scope) or find(name, s) or find(perm_scope, s)
                    if r:
                        click(r); s = wait(0.8)
                        s = snap()
                confirm_ref = find_exact_button("确认", s) or find_exact_button("确定", s) or find_exact_button("确认开通", s)
                if confirm_ref:
                    click(confirm_ref); s = wait(2)
                    s = snap()
        if scope in ("user", "all"):
            # 切换到「用户身份权限 user_access_token」并勾选
            user_tab = find("用户身份权限", s) or find("user_access_token", s)
            if user_tab:
                click(user_tab); s = wait(2)
                s = snap()
            USER_PERM_LIST = [
                ("获取用户 user ID", "contact:user.employee_id:readonly"),
            ]
            for name, perm_scope in USER_PERM_LIST:
                search_ref = find_input_after("搜索", s) or find_input_after("例如", s) or find_first_input(s)
                if search_ref:
                    fill(search_ref, name); s = wait(2)
                s = snap()
                result = click_permission_checkbox_by_js(name)
                if result == "already_checked":
                    continue
                if result == "clicked":
                    s = wait(1)
                else:
                    if is_permission_checked_by_js(name):
                        continue
                    r = find_checkbox_or_ref_for_permission(s, name, perm_scope) or find(name, s) or find(perm_scope, s)
                    if r:
                        click(r); s = wait(1)
                        s = snap()
                confirm_ref = find_exact_button("确认", s) or find_exact_button("确定", s) or find_exact_button("确认开通", s)
                if confirm_ref:
                    click(confirm_ref); s = wait(2)
                    s = snap()
        # 勾选完成后下滑页面，点击「确认开通权限」
        _scroll_to_bottom(s)
        s = snap()
        confirm_btn = find_exact_button("确认开通权限", s) or find("确认开通权限", s)
        if confirm_btn:
            click(confirm_btn); s = wait(3)
            s = snap()

    # 配置完权限后重新打开页面并进入应用，避免弹窗/浮层关不掉阻塞后续步骤
    s = snap()
    nav(FEISHU_URL); s = wait(3)
    if _is_logged_in(s):
        list_ref = find("我的应用", s) or find("My Apps", s)
        if list_ref:
            click(list_ref); s = wait(2)
        s = snap()
        existing_refs = find_refs_exact(app_name, s)
        if existing_refs:
            preferred = _refs_with_tag(existing_refs, s, ["a", "link", "div", "button"])
            ref_to_click = preferred[0] if preferred else existing_refs[0]
            click(ref_to_click); s = wait(3)
    s = snap()

    # 已屏蔽：批量导入/导出权限
    # s = click_text("批量导入/导出权限", s); s = wait(2)
    # if "批量导入" not in s:
    #     s = click_text("批量导入权限", s); s = wait(2)
    # ...
    out({"status": "permissions_imported"})

def _scroll_to_bottom(s):
    """滚动页面到底部，使「保存」等按钮进入视口。先尝试 browser_scroll_down，再辅以 PageDown 键。"""
    for _ in range(6):
        call("browser_scroll_down", {})
        time.sleep(0.25)
    for _ in range(6):
        press_key("PageDown")
        time.sleep(0.2)

def _do_publish(version="1.0.0"):
    s = snap()
    s = click_text("版本管理与发布", s) or click_text("版本管理", s); s = wait(3)
    s = click_text("创建版本", s) or click_text("新建版本", s); s = wait(2)

    ver_ref = find_input_after("应用版本号", s)
    if ver_ref:
        fill(ver_ref, version); time.sleep(0.5); s = wait(1)

    note_ref = find_input_after("更新说明", s)
    if note_ref:
        fill(note_ref, "初始版本"); time.sleep(0.5); s = wait(1)

    # 下滑滚动条到底部
    _scroll_to_bottom(s)
    s = snap()  # 滚动后重新取快照，使「保存」进入可点击列表
    ref = find("保存", s)
    if not ref:
        out({"status": "error", "message": "保存按钮未找到"})
        return
    click(ref); s = wait(2)
    
    s = click_text("申请发布", s) or click_text("确认发布", s); s = wait(3)
    ref = find("确定", s) or find("确认发布", s) or find("申请线上发布", s)
    if ref: click(ref); s = wait(3);

def publish_app():
    _do_publish('1.0.0')
    out({"status": "published"})

def publish_app_step2():
    _do_publish('1.0.1')
    out({"status": "published"})

# ── CLI ───────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("open_login")
    sub.add_parser("check_login")
    cp = sub.add_parser("create_app"); cp.add_argument("--name", default="ScienceClaw 助手")
    sub.add_parser("add_bot")
    sub.add_parser("publish_app")
    sub.add_parser("get_credentials")
    sub.add_parser("configure_events")
    cp_perm = sub.add_parser("configure_permissions")
    cp_perm.add_argument("--name", default="ScienceClaw 助手")
    cp_perm.add_argument("--scope", choices=["app", "user", "all"], default="all", help="app=仅应用身份权限, user=仅用户身份权限, all=全部")
    sub.add_parser("publish_app_step2")
    a = p.parse_args()
    if not a.cmd: p.print_help(); sys.exit(1)
    try:
        {"open_login": open_login, "check_login": check_login,
         "create_app": lambda: create_app(a.name), "add_bot": add_bot,
         "publish_app": publish_app,
         "get_credentials": get_credentials, "configure_events": configure_events,
         "configure_permissions": lambda: configure_permissions(getattr(a, "name", "ScienceClaw 助手"), getattr(a, "scope", "all")),
         "publish_app_step2": publish_app_step2
        }[a.cmd]()
    except Exception as e:
        out({"status": "error", "command": a.cmd, "message": str(e)}); sys.exit(1)

if __name__ == "__main__":
    main()
