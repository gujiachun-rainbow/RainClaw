from __future__ import annotations

import asyncio
import threading
from typing import Optional

from loguru import logger

from backend.im.adapters.lark import LarkAdapter, lark
from backend.im.base import IMPlatform, IMMessage
from backend.im.orchestrator import IMServiceOrchestrator


class LarkLongConnectionService:
    def __init__(self, orchestrator: IMServiceOrchestrator, adapter: LarkAdapter):
        self.orchestrator = orchestrator
        self.adapter = adapter
        self._client = None
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws_loop: Optional[asyncio.AbstractEventLoop] = None
        self._running = False
        self._stopping = False
        self._state_lock = threading.RLock()

    async def start(self):
        with self._state_lock:
            if self._running:
                return
        if lark is None:
            raise RuntimeError("lark-oapi is required for lark long connection")
        loop = asyncio.get_running_loop()
        event_handler = self.adapter.build_long_connection_handler(self._on_message)
        ws_client_module = getattr(lark.ws, "client", None)
        with self._state_lock:
            self._loop = loop
            self._client = None
            self._ws_loop = None
            self._running = True
            self._stopping = False

        def _run():
            ws_loop = asyncio.new_event_loop()
            original_ws_module_loop = None
            try:
                asyncio.set_event_loop(ws_loop)
                if ws_client_module is not None and hasattr(ws_client_module, "loop"):
                    original_ws_module_loop = ws_client_module.loop
                    ws_client_module.loop = ws_loop
                client = lark.ws.Client(
                    self.adapter.app_id,
                    self.adapter.app_secret,
                    event_handler=event_handler,
                    log_level=lark.LogLevel.INFO,
                )
                with self._state_lock:
                    self._client = client
                    self._ws_loop = ws_loop
                client.start()
            except Exception as exc:
                if not self._stopping:
                    logger.exception(f"lark long connection stopped unexpectedly: {exc}")
            finally:
                if ws_client_module is not None and hasattr(ws_client_module, "loop"):
                    ws_client_module.loop = (
                        original_ws_module_loop
                        if original_ws_module_loop is not None
                        else asyncio.new_event_loop()
                    )
                if not ws_loop.is_closed():
                    ws_loop.close()
                with self._state_lock:
                    self._running = False
                    self._thread = None
                    self._client = None
                    self._ws_loop = None
                    self._stopping = False

        thread = threading.Thread(target=_run, daemon=True, name="lark-ws-client")
        with self._state_lock:
            self._thread = thread
        thread.start()
        logger.info("lark long connection started")

    async def stop(self):
        with self._state_lock:
            running = self._running
            thread = self._thread
            client = self._client
            ws_loop = self._ws_loop
            self._running = False
            self._stopping = True
            self._loop = None
            self._ws_loop = None
        if not running and (thread is None or not thread.is_alive()):
            return
        if client and ws_loop and not ws_loop.is_closed():
            try:
                if hasattr(client, "_disconnect"):
                    disconnect_future = asyncio.run_coroutine_threadsafe(client._disconnect(), ws_loop)
                    disconnect_future.result(3)
            except Exception as exc:
                logger.warning(f"disconnect lark long connection failed: {exc}")
            try:
                ws_loop.call_soon_threadsafe(ws_loop.stop)
            except Exception as exc:
                logger.warning(f"stop lark ws loop failed: {exc}")
        try:
            if client and hasattr(client, "stop"):
                client.stop()
        except Exception as exc:
            logger.warning(f"stop lark long connection failed: {exc}")
        if thread and thread.is_alive():
            await asyncio.to_thread(thread.join, 5)
            if thread.is_alive():
                logger.warning("lark long connection thread did not exit within timeout")
        with self._state_lock:
            if self._thread is thread:
                self._thread = None
            self._client = None
            self._stopping = False
        logger.info("lark long connection stopped")

    def _on_message(self, message: IMMessage):
        loop = self._loop
        if not loop or loop.is_closed():
            return
        try:
            future = asyncio.run_coroutine_threadsafe(
                self.orchestrator.handle_incoming_message(IMPlatform.LARK, message),
                loop,
            )
        except RuntimeError as exc:
            logger.warning(f"dispatch lark message ignored due to loop state: {exc}")
            return

        def _on_done(fut):
            try:
                fut.result()
            except Exception as exc:
                logger.exception(f"dispatch lark message failed: {exc}")

        future.add_done_callback(_on_done)
