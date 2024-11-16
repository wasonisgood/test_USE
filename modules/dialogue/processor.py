# modules/dialogue/processor.py

import logging
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

class DialogueProcessor:
    def __init__(self):
        self.dialogues_dir = BASE_DIR / "data" / "dialogues"
        self.dialogues_dir.mkdir(parents=True, exist_ok=True)
        self.current_dialogue = None
        self.dialogue_history = []

    def process_dialogue(self, dialogue_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理對話數據"""
        try:
            processed_dialogue = {
                'id': f"dialogue_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'dialogue': []
            }

            # 處理每個對話段落
            for entry in dialogue_data['dialogue']:
                processed_entry = self._process_dialogue_entry(entry)
                processed_dialogue['dialogue'].append(processed_entry)

            # 保存處理後的對話
            self._save_dialogue(processed_dialogue)
            self.current_dialogue = processed_dialogue
            self.dialogue_history.append(processed_dialogue['id'])

            logger.info(f"對話處理完成: {processed_dialogue['id']}")
            return processed_dialogue

        except Exception as e:
            logger.error(f"處理對話失敗: {e}")
            raise

    def _process_dialogue_entry(self, entry: Dict[str, str]) -> Dict[str, Any]:
        """處理單個對話條目"""
        try:
            # 添加額外的處理邏輯，例如：
            # - 情感分析
            # - 關鍵詞提取
            # - 時間標記等
            processed_entry = {
                'id': entry['id'],
                'user': entry['User'],
                'text': entry['text'],
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'word_count': len(entry['text']),
                    'processed': True
                }
            }
            return processed_entry

        except Exception as e:
            logger.error(f"處理對話條目失敗: {e}")
            raise

    def _save_dialogue(self, dialogue: Dict[str, Any]):
        """保存對話數據"""
        try:
            file_path = self.dialogues_dir / f"{dialogue['id']}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dialogue, f, ensure_ascii=False, indent=2)
            logger.debug(f"對話已保存: {file_path}")

        except Exception as e:
            logger.error(f"保存對話失敗: {e}")
            raise

    def get_dialogue_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取對話歷史"""
        try:
            history = []
            for dialogue_id in reversed(self.dialogue_history[-limit:]):
                dialogue_data = self.load_dialogue(dialogue_id)
                if dialogue_data:
                    history.append(dialogue_data)
            return history

        except Exception as e:
            logger.error(f"獲取對話歷史失敗: {e}")
            return []

    def load_dialogue(self, dialogue_id: str) -> Optional[Dict[str, Any]]:
        """加載特定對話"""
        try:
            file_path = self.dialogues_dir / f"{dialogue_id}.json"
            if not file_path.exists():
                logger.warning(f"對話文件不存在: {dialogue_id}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"加載對話失敗: {e}")
            return None

    def analyze_dialogue(self, dialogue_id: str) -> Dict[str, Any]:
        """分析對話內容"""
        try:
            dialogue = self.load_dialogue(dialogue_id)
            if not dialogue:
                return {}

            analysis = {
                'total_entries': len(dialogue['dialogue']),
                'users': {},
                'word_count': 0,
                'average_length': 0
            }

            # 分析對話內容
            for entry in dialogue['dialogue']:
                user = entry['user']
                text = entry['text']
                
                if user not in analysis['users']:
                    analysis['users'][user] = {
                        'message_count': 0,
                        'total_words': 0
                    }

                analysis['users'][user]['message_count'] += 1
                analysis['users'][user]['total_words'] += len(text)
                analysis['word_count'] += len(text)

            # 計算平均長度
            if analysis['total_entries'] > 0:
                analysis['average_length'] = analysis['word_count'] / analysis['total_entries']

            return analysis

        except Exception as e:
            logger.error(f"分析對話失敗: {e}")
            return {}

    def search_dialogues(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索對話內容"""
        try:
            results = []
            for file_path in self.dialogues_dir.glob('*.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        dialogue = json.load(f)
                        
                    # 搜索對話內容
                    matched_entries = [
                        entry for entry in dialogue['dialogue']
                        if keyword.lower() in entry['text'].lower()
                    ]
                    
                    if matched_entries:
                        results.append({
                            'dialogue_id': dialogue['id'],
                            'timestamp': dialogue['timestamp'],
                            'matched_entries': matched_entries
                        })
                        
                except Exception as e:
                    logger.error(f"處理文件失敗 {file_path}: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"搜索對話失敗: {e}")
            return []

    def cleanup_old_dialogues(self, days: int = 30):
        """清理舊的對話文件"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for file_path in self.dialogues_dir.glob('*.json'):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    logger.info(f"刪除舊對話文件: {file_path}")

        except Exception as e:
            logger.error(f"清理舊對話失敗: {e}")