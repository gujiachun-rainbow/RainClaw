#!/usr/bin/env python3
"""One-shot Feishu setup wrapper built on top of feishu_auto_setup.py."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_AUTO_SCRIPT = Path("/builtin-skills/feishu-setup/scripts/feishu_auto_setup.py")
DEFAULT_BACKEND_URL = "http://backend:8000/api/v1/im/internal/feishu-setup"


class SetupError(RuntimeError):
    def __init__(self, step: str, message: str, details: Any | None = None):
        super().__init__(message)
        self.step = step
        self.message = message
        self.details = details


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def out(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False), flush=True)


def parse_json_output(text: str) -> dict[str, Any] | None:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def resolve_auto_script(explicit_path: str | None) -> Path:
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())

    here = Path(__file__).resolve()
    candidates.extend([
        here.with_name("feishu_auto_setup.py"),
        DEFAULT_AUTO_SCRIPT,
    ])

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    raise SetupError(
        "bootstrap",
        "未找到 feishu_auto_setup.py，请通过 --auto-script 指定路径，或确保 /builtin-skills 已挂载",
        {"candidates": [str(path) for path in candidates]},
    )


def run_auto_step(
    auto_script: Path,
    command: str,
    *args: str,
    expected_status: set[str] | None = None,
) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(auto_script), command, *args],
        cwd=str(auto_script.parent),
        capture_output=True,
        text=True,
    )
    payload = parse_json_output(proc.stdout)
    stderr = (proc.stderr or "").strip()

    if payload is None:
        raise SetupError(
            command,
            "子命令未返回可解析的 JSON",
            {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": stderr},
        )

    status = str(payload.get("status", ""))
    if proc.returncode != 0 or status == "error":
        raise SetupError(
            command,
            payload.get("message") or f"{command} 执行失败",
            {"returncode": proc.returncode, "payload": payload, "stderr": stderr},
        )

    if expected_status and status not in expected_status:
        raise SetupError(
            command,
            f"{command} 返回了非预期状态: {status}",
            {"payload": payload, "stderr": stderr},
        )

    return payload


def run_with_retries(
    step_label: str,
    runner,
    *,
    retries: int,
) -> dict[str, Any]:
    last_error: SetupError | None = None
    for attempt in range(retries + 1):
        try:
            return runner()
        except SetupError as exc:
            last_error = exc
            if attempt >= retries:
                raise
            log(f"[{step_label}] 第 {attempt + 1} 次失败，准备重试: {exc.message}")
    assert last_error is not None
    raise last_error


def wait_for_login(auto_script: Path, timeout_seconds: int, interval_seconds: int) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        payload = run_auto_step(auto_script, "check_login", expected_status={"logged_in", "not_logged_in"})
        if payload["status"] == "logged_in":
            log("[login] 已确认登录成功")
            return
        remaining = max(0, int(deadline - time.monotonic()))
        log(f"[login] 等待扫码登录，剩余 {remaining}s")
        time.sleep(interval_seconds)

    raise SetupError("check_login", "等待飞书扫码登录超时，请重新执行并完成扫码")


def configure_backend(backend_url: str, app_id: str, app_secret: str, timeout_seconds: int) -> dict[str, Any]:
    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode("utf-8")
    req = request.Request(
        backend_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SetupError(
            "backend_setup",
            f"后端配置请求失败: HTTP {exc.code}",
            {"response": raw},
        ) from exc
    except error.URLError as exc:
        raise SetupError(
            "backend_setup",
            "无法连接后端配置接口，请确认 sandbox 可访问 backend:8000",
            {"reason": str(exc.reason)},
        ) from exc

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SetupError("backend_setup", "后端配置接口返回了非 JSON 数据", {"response": raw}) from exc

    if payload.get("code") not in (None, 0):
        raise SetupError("backend_setup", payload.get("msg") or "后端配置接口返回错误", payload)

    data = payload.get("data") or {}
    if data.get("saved") is not True:
        raise SetupError("backend_setup", "后端未确认保存飞书凭证", payload)
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="ScienceClaw 助手")
    parser.add_argument("--auto-script", help="feishu_auto_setup.py 路径；默认自动探测")
    parser.add_argument("--backend-url", default=DEFAULT_BACKEND_URL)
    parser.add_argument("--login-timeout", type=int, default=300, help="等待扫码登录的最长秒数")
    parser.add_argument("--login-interval", type=int, default=5, help="轮询登录状态的间隔秒数")
    parser.add_argument("--request-timeout", type=int, default=30, help="后端请求超时时间（秒）")
    parser.add_argument("--max-retries", type=int, default=1, help="页面类步骤失败后的额外重试次数")
    parser.add_argument("--skip-app-permissions", action="store_true")
    parser.add_argument("--skip-user-permissions", action="store_true")
    parser.add_argument("--skip-step2-publish", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    auto_script = resolve_auto_script(args.auto_script)

    summary: dict[str, Any] = {
        "app_name": args.name,
        "auto_script": str(auto_script),
        "permissions": {"app": not args.skip_app_permissions, "user": not args.skip_user_permissions},
        "step2_publish": not args.skip_step2_publish,
    }

    try:
        log("[1/8] 打开飞书登录页")
        login_payload = run_auto_step(auto_script, "open_login", expected_status={"waiting_for_login", "already_logged_in"})
        if login_payload["status"] == "waiting_for_login":
            log(login_payload.get("message") or "请在浏览器面板扫码登录飞书")
        wait_for_login(auto_script, timeout_seconds=args.login_timeout, interval_seconds=args.login_interval)

        log("[2/8] 创建或打开应用")
        app_payload = run_with_retries(
            "create_app",
            lambda: run_auto_step(auto_script, "create_app", "--name", args.name, expected_status={"created", "opened"}),
            retries=args.max_retries,
        )
        summary["create_app_status"] = app_payload["status"]

        log("[3/8] 添加机器人并执行首次发布")
        bot_payload = run_with_retries(
            "add_bot",
            lambda: run_auto_step(auto_script, "add_bot", expected_status={"bot_added", "bot_already_added"}),
            retries=args.max_retries,
        )
        summary["bot_status"] = bot_payload["status"]
        run_with_retries(
            "publish_app",
            lambda: run_auto_step(auto_script, "publish_app", expected_status={"published"}),
            retries=args.max_retries,
        )

        log("[4/8] 获取应用凭证")
        credentials = run_with_retries(
            "get_credentials",
            lambda: run_auto_step(auto_script, "get_credentials", expected_status={"ok"}),
            retries=args.max_retries,
        )
        app_id = credentials.get("app_id")
        app_secret = credentials.get("app_secret")
        if not app_id or not app_secret:
            raise SetupError(
                "get_credentials",
                "未能获取完整的 App ID / App Secret，请按提示手动处理后重试",
                credentials,
            )
        summary["app_id"] = app_id

        log("[5/8] 回写系统配置并建立飞书长连接")
        backend_payload = configure_backend(args.backend_url, app_id, app_secret, timeout_seconds=args.request_timeout)
        summary["backend_setup"] = backend_payload.get("data")

        log("[6/8] 配置事件与回调")
        events_payload = run_with_retries(
            "configure_events",
            lambda: run_auto_step(auto_script, "configure_events", expected_status={"events_configured"}),
            retries=args.max_retries,
        )
        summary["events_status"] = events_payload["status"]


        log("[7/8] 配置权限")
        if args.skip_app_permissions:
            summary["app_permissions_status"] = "skipped"
        else:
            app_perm_payload = run_with_retries(
                "configure_permissions_app",
                lambda: run_auto_step(
                    auto_script,
                    "configure_permissions",
                    "--name",
                    args.name,
                    "--scope",
                    "app",
                    expected_status={"permissions_imported"},
                ),
                retries=args.max_retries,
            )
            summary["app_permissions_status"] = app_perm_payload["status"]

        if args.skip_user_permissions:
            summary["user_permissions_status"] = "skipped"
        else:
            user_perm_payload = run_with_retries(
                "configure_permissions_user",
                lambda: run_auto_step(
                    auto_script,
                    "configure_permissions",
                    "--name",
                    args.name,
                    "--scope",
                    "user",
                    expected_status={"permissions_imported"},
                ),
                retries=args.max_retries,
            )
            summary["user_permissions_status"] = user_perm_payload["status"]


        log("[8/8] 第二次发布")
        if args.skip_step2_publish:
            summary["step2_publish_status"] = "skipped"
        else:
            publish_step2_payload = run_with_retries(
                "publish_app_step2",
                lambda: run_auto_step(auto_script, "publish_app_step2", expected_status={"published"}),
                retries=args.max_retries,
            )
            summary["step2_publish_status"] = publish_step2_payload["status"]

        out({"status": "completed", "summary": summary})
    except SetupError as exc:
        out({"status": "error", "step": exc.step, "message": exc.message, "details": exc.details})
        sys.exit(1)


if __name__ == "__main__":
    main()
