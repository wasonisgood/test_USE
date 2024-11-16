# modules/utils/file_handler.py

import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import mimetypes
from uuid import uuid4
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

class FileHandler:
    UPLOAD_DIR = BASE_DIR / "data" / "uploads"
    ALLOWED_EXTENSIONS = {'.txt', '.csv', '.json', '.pdf', '.docx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    def __init__(self):
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_data: bytes, original_filename: str) -> Dict[str, Any]:
        """保存上傳的文件"""
        try:
            # 檢查文件大小
            if len(file_data) > self.MAX_FILE_SIZE:
                raise ValueError("文件太大，超過大小限制")

            # 獲取文件擴展名並檢查
            suffix = Path(original_filename).suffix.lower()
            if suffix not in self.ALLOWED_EXTENSIONS:
                raise ValueError(f"不支持的文件類型: {suffix}")

            # 生成唯一文件名
            unique_filename = f"{uuid4()}{suffix}"
            file_path = self.UPLOAD_DIR / unique_filename

            # 保存文件
            with open(file_path, 'wb') as f:
                f.write(file_data)

            return {
                "status": "success",
                "original_name": original_filename,
                "saved_name": unique_filename,
                "file_path": str(file_path),
                "file_type": suffix[1:],
                "size": len(file_data)
            }

        except Exception as e:
            logger.error(f"保存文件失敗: {e}")
            raise

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """獲取文件信息"""
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            return {
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "type": mimetypes.guess_type(str(file_path))[0],
                "last_modified": file_path.stat().st_mtime
            }

        except Exception as e:
            logger.error(f"獲取文件信息失敗: {e}")
            raise

    def delete_file(self, file_path: Path) -> bool:
        """刪除文件"""
        try:
            if not file_path.exists():
                return False

            file_path.unlink()
            return True

        except Exception as e:
            logger.error(f"刪除文件失敗: {e}")
            return False

    def list_files(self) -> List[Dict[str, Any]]:
        """列出上傳的文件"""
        try:
            files = []
            for file_path in self.UPLOAD_DIR.glob('*'):
                if file_path.is_file():
                    files.append(self.get_file_info(file_path))
            return files

        except Exception as e:
            logger.error(f"列出文件失敗: {e}")
            return []

