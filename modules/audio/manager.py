# modules/audio/manager.py

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import asyncio
from config.settings import AUDIO_DIR, AUDIO_CLEANUP_INTERVAL, AUDIO_MAX_AGE

logger = logging.getLogger(__name__)

class AudioFileManager:
    def __init__(self):
        self.audio_dir = AUDIO_DIR
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.audio_dir / "audio_metadata.json"
        self.metadata = self._load_metadata()
        self._cleanup_task = None

    def _load_metadata(self) -> Dict[str, Any]:
        """加載音訊文件元數據"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"加載音訊元數據失敗: {e}")
            return {}

    def _save_metadata(self):
        """保存音訊文件元數據"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.debug("音訊元數據已保存")
        except Exception as e:
            logger.error(f"保存音訊元數據失敗: {e}")

    def register_audio(self, file_name: str, metadata: Dict[str, Any]) -> str:
        """註冊新的音訊文件"""
        try:
            audio_id = f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            file_path = self.audio_dir / audio_id

            self.metadata[audio_id] = {
                'original_name': file_name,
                'created_at': datetime.now().isoformat(),
                'file_path': str(file_path),
                'size': 0,  # 將在文件保存後更新
                'metadata': metadata,
                'status': 'registered'
            }
            
            self._save_metadata()
            logger.info(f"註冊音訊文件: {audio_id}")
            return audio_id

        except Exception as e:
            logger.error(f"註冊音訊文件失敗: {e}")
            raise

    def save_audio_file(self, audio_id: str, audio_data: bytes) -> bool:
        """保存音訊文件"""
        try:
            if audio_id not in self.metadata:
                raise ValueError(f"未找到音訊記錄: {audio_id}")

            file_path = Path(self.metadata[audio_id]['file_path'])
            
            with open(file_path, 'wb') as f:
                f.write(audio_data)

            # 更新元數據
            self.metadata[audio_id].update({
                'size': len(audio_data),
                'status': 'saved',
                'saved_at': datetime.now().isoformat()
            })
            
            self._save_metadata()
            logger.info(f"保存音訊文件: {audio_id}")
            return True

        except Exception as e:
            logger.error(f"保存音訊文件失敗: {e}")
            return False

    def get_audio_info(self, audio_id: str) -> Optional[Dict[str, Any]]:
        """獲取音訊文件信息"""
        try:
            if audio_id not in self.metadata:
                return None

            info = self.metadata[audio_id].copy()
            file_path = Path(info['file_path'])
            
            if file_path.exists():
                info['exists'] = True
                info['actual_size'] = file_path.stat().st_size
            else:
                info['exists'] = False

            return info

        except Exception as e:
            logger.error(f"獲取音訊信息失敗: {e}")
            return None

    def delete_audio(self, audio_id: str) -> bool:
        """刪除音訊文件"""
        try:
            if audio_id not in self.metadata:
                return False

            file_path = Path(self.metadata[audio_id]['file_path'])
            
            if file_path.exists():
                file_path.unlink()

            del self.metadata[audio_id]
            self._save_metadata()
            
            logger.info(f"刪除音訊文件: {audio_id}")
            return True

        except Exception as e:
            logger.error(f"刪除音訊文件失敗: {e}")
            return False

    async def start_cleanup_task(self):
        """啟動定期清理任務"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("啟動音訊文件清理任務")

    async def stop_cleanup_task(self):
        """停止清理任務"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("停止音訊文件清理任務")

    async def _cleanup_loop(self):
        """定期清理過期文件的循環"""
        while True:
            try:
                self.cleanup_old_files()
                await asyncio.sleep(AUDIO_CLEANUP_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理任務執行失敗: {e}")
                await asyncio.sleep(60)  # 發生錯誤時等待較短時間後重試

    def cleanup_old_files(self):
        """清理過期的音訊文件"""
        try:
            current_time = datetime.now()
            files_to_delete = []

            for audio_id, info in self.metadata.items():
                try:
                    created_at = datetime.fromisoformat(info['created_at'])
                    if (current_time - created_at) > timedelta(seconds=AUDIO_MAX_AGE):
                        files_to_delete.append(audio_id)
                except Exception as e:
                    logger.error(f"處理文件時間失敗 {audio_id}: {e}")

            for audio_id in files_to_delete:
                self.delete_audio(audio_id)

            logger.info(f"清理了 {len(files_to_delete)} 個過期音訊文件")

        except Exception as e:
            logger.error(f"清理過期文件失敗: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """獲取存儲統計信息"""
        try:
            total_files = len(self.metadata)
            total_size = sum(
                Path(info['file_path']).stat().st_size
                for info in self.metadata.values()
                if Path(info['file_path']).exists()
            )

            return {
                'total_files': total_files,
                'total_size': total_size,
                'available_space': shutil.disk_usage(self.audio_dir).free
            }

        except Exception as e:
            logger.error(f"獲取存儲統計失敗: {e}")
            return {
                'total_files': 0,
                'total_size': 0,
                'available_space': 0
            }

    def validate_audio_files(self) -> List[str]:
        """驗證所有音訊文件的完整性"""
        invalid_files = []
        for audio_id, info in self.metadata.items():
            try:
                file_path = Path(info['file_path'])
                if not file_path.exists():
                    invalid_files.append(audio_id)
                elif file_path.stat().st_size == 0:
                    invalid_files.append(audio_id)
            except Exception as e:
                logger.error(f"驗證文件失敗 {audio_id}: {e}")
                invalid_files.append(audio_id)

        return invalid_files

    async def optimize_storage(self):
        """優化存儲空間"""
        try:
            # 清理無效文件
            invalid_files = self.validate_audio_files()
            for audio_id in invalid_files:
                self.delete_audio(audio_id)

            # 整理存儲空間
            self._save_metadata()  # 重新保存整理後的元數據
            
            logger.info(f"存儲優化完成，清理了 {len(invalid_files)} 個無效文件")
            
        except Exception as e:
            logger.error(f"優化存儲空間失敗: {e}")

    def get_audio_file_path(self, audio_id: str) -> Optional[Path]:
        """獲取音訊文件路徑"""
        try:
            if audio_id not in self.metadata:
                return None
                
            file_path = Path(self.metadata[audio_id]['file_path'])
            return file_path if file_path.exists() else None
            
        except Exception as e:
            logger.error(f"獲取文件路徑失敗: {e}")
            return None