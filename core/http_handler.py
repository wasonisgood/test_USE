# core/http_handler.py

import logging
import json
from http.server import SimpleHTTPRequestHandler
from typing import Optional, Dict, Any
from pathlib import Path
import urllib.parse
from config.settings import STATIC_DIR, AUDIO_DIR

logger = logging.getLogger(__name__)

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        """處理 GET 請求"""
        try:
            # 解碼 URL
            parsed_path = urllib.parse.unquote(self.path)
            
            # 處理音頻文件請求
            if parsed_path.startswith('/audio/'):
                self.serve_audio_file(parsed_path)
                return
            
            # 其他靜態文件
            super().do_GET()
            
        except Exception as e:
            logger.error(f"處理 GET 請求失敗: {e}")
            self.send_error(500, str(e))

    def serve_audio_file(self, path):
        """處理音頻文件請求"""
        try:
            # 從路徑中提取文件名
            file_name = path.replace('/audio/', '', 1)
            file_path = AUDIO_DIR / file_name
            
            logger.debug(f"請求音頻文件: {file_path}")
            
            if not file_path.exists():
                logger.error(f"音頻文件不存在: {file_path}")
                self.send_error(404, "File not found")
                return
            
            # 設置正確的 MIME 類型
            self.send_response(200)
            self.send_header('Content-Type', 'audio/mpeg')
            self.send_header('Content-Length', str(file_path.stat().st_size))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 讀取並發送文件內容
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
                
            logger.debug(f"成功發送音頻文件: {file_path}")
            
        except Exception as e:
            logger.error(f"處理音頻文件失敗: {e}")
            self.send_error(500, str(e))

    def translate_path(self, path):
        """路徑轉換"""
        # 先解碼路徑
        path = urllib.parse.unquote(path)
        
        if path.startswith('/audio/'):
            return str(AUDIO_DIR / path.replace('/audio/', '', 1))
        return super().translate_path(path)

    def end_headers(self):
        """添加 CORS 頭"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()