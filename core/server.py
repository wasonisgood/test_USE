# core/server.py

import asyncio
import websockets
import logging
from pathlib import Path
from http.server import HTTPServer
from threading import Thread
from typing import Optional
from config.settings import (
    WEBSOCKET_HOST,
    WEBSOCKET_PORT,
    HTTP_PORT,
    LOG_FORMAT,
    LOG_LEVEL
)
from core.websocket import WebSocketHandler
from core.http_handler import CustomHTTPRequestHandler
from modules.ollama.checker import HardwareChecker

logger = logging.getLogger(__name__)

class PodcastServer:
    def __init__(self):
        self._setup_logging()
        self.websocket_handler = WebSocketHandler()
        self.http_server: Optional[HTTPServer] = None
        self.http_thread: Optional[Thread] = None
        self.use_local = HardwareChecker.is_local_environment_ready()

    def _setup_logging(self):
        """設置日誌系統"""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/server.log', encoding='utf-8')
            ]
        )

    def run_http_server(self):
        """運行 HTTP 服務器"""
        try:
            server_address = ('', HTTP_PORT)
            self.http_server = HTTPServer(server_address, CustomHTTPRequestHandler)
            logger.info(f"HTTP 服務器啟動於 port {HTTP_PORT}")
            self.http_server.serve_forever()
        except Exception as e:
            logger.error(f"HTTP 服務器啟動失敗: {e}")
            raise

    async def run_websocket_server(self):
        """運行 WebSocket 服務器"""
        try:
            async with websockets.serve(
                self.websocket_handler.handle_connection,
                WEBSOCKET_HOST,
                WEBSOCKET_PORT
            ):
                logger.info(f"WebSocket 服務器啟動於 {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
                await asyncio.Future()  # 保持運行
        except Exception as e:
            logger.error(f"WebSocket 服務器啟動失敗: {e}")
            raise

    def start(self):
        """啟動服務器"""
        try:
            # 啟動 HTTP 服務器
            self.http_thread = Thread(target=self.run_http_server, daemon=True)
            self.http_thread.start()

            # 啟動 WebSocket 服務器
            asyncio.run(self.run_websocket_server())
            logger.info(f"服務器啟動，使用 Ollama: {'是' if self.use_ollama else '否'}")
            super().start()
        except KeyboardInterrupt:
            logger.info("服務器正在關閉...")
        except Exception as e:
            logger.error(f"服務器啟動失敗: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self):
        """清理資源"""
        try:
            if self.http_server:
                self.http_server.shutdown()
            logger.info("服務器已關閉")
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {e}")