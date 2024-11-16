import json
import logging
from openai import OpenAI
from config.settings import OPENAI_API_KEY, GPT_MODEL, OPENAI_API_MAX_TOKENS

logger = logging.getLogger(__name__)

class DialogueGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate(self, topic: str, context: str = None, target_duration_minutes: int = 8) -> dict:
        """
        生成對話內容（多輪對話）
        
        Args:
            topic: 對話主題
            context: 額外的上下文信息（例如從RAG獲得的信息）
            target_duration_minutes: 目標對話時長（分鐘），默認8分鐘
        
        Returns:
            dict: 包含多輪對話內容的字典
        """
        try:
            system_prompt = self._get_system_prompt(context)
            dialogue = []
            total_duration = 0  # 總時長（秒）
            avg_time_per_round = 45  # 每輪對話的平均時長（秒）

            while total_duration < target_duration_minutes * 60:
                # 生成新一輪對話
                response = self._create_chat_completion(system_prompt, topic, len(dialogue))
                new_dialogue = json.loads(response.choices[0].message.content)["dialogue"]

                # 更新短期記憶
                dialogue.extend(new_dialogue)
                total_duration += len(new_dialogue) * avg_time_per_round

                # 檢查是否需要截斷以符合Token限制
                dialogue = self._truncate_dialogue(dialogue)

                # 若時長不足且接近Token限制，生成額外對話
                if total_duration < target_duration_minutes * 60:
                    logger.info(f"對話時長不足，繼續生成下一輪對話...")

            return {"dialogue": dialogue}
        except Exception as e:
            logger.error(f"生成對話失敗: {e}")
            raise

    def _get_system_prompt(self, context: str = None) -> str:
        """生成系統提示"""
        base_prompt = """您是一個專業的 Podcast 製作人,負責創建男女對話的腳本。請遵循以下規則:

1. 創建兩個角色的對話：男性（M）和女性（F）
2. 每句對話以"M:"或"F:"開頭
3. 每段對話保持在40-60個字之間
4. 使用輕鬆、自然的口語化表達
5. 如有專業話題,用簡單易懂的方式解釋
6. 對話要生動有趣,富有互動性
7. 每輪至少生成50個來回的對話

輸出格式為JSON:
{
  "dialogue": [
    {"id": 1, "User": "M", "text": "..."},
    {"id": 2, "User": "F", "text": "..."}
  ]
}"""

        if context:
            base_prompt += f"\n\n請參考以下資訊作為對話內容的依據:\n{context}"

        return base_prompt

    def _create_chat_completion(self, system_prompt: str, topic: str, previous_rounds: int = 0):
        """創建對話完成"""
        try:
            return self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"請基於主題「{topic}」創建第 {previous_rounds + 1} 輪對話。"
                    }
                ],
                temperature=0.7,
                max_tokens=OPENAI_API_MAX_TOKENS
            )
        except Exception as e:
            logger.error(f"創建對話完成時發生錯誤: {e}")
            raise

    def _truncate_dialogue(self, dialogue: list) -> list:
        """將對話內容截斷至 OpenAI API 的最大 token 數"""
        total_tokens = sum(len(entry["text"].split()) for entry in dialogue)
        if total_tokens > OPENAI_API_MAX_TOKENS:
            logger.warning(f"對話內容超過 OpenAI API 的最大 token 數 ({OPENAI_API_MAX_TOKENS}), 將進行截斷")
            
            truncated_dialogue = []
            current_tokens = 0
            for entry in dialogue:
                entry_tokens = len(entry["text"].split())
                if current_tokens + entry_tokens <= OPENAI_API_MAX_TOKENS:
                    truncated_dialogue.append(entry)
                    current_tokens += entry_tokens
                else:
                    break
            
            return truncated_dialogue
        else:
            return dialogue
