import json
import logging
import ollama
from modules.ollama.checker import HardwareChecker
from openai import OpenAI
from config.settings import OPENAI_API_KEY, GPT_MODEL, OPENAI_API_MAX_TOKENS

logger = logging.getLogger(__name__)

class DialogueGenerator:
    def __init__(self):
        """
        初始化對話生成器，檢查硬件條件並決定使用本地或雲端方案
        """
        self.use_local = HardwareChecker.is_local_environment_ready()
        self.use_local = False  # Force cloud usage for now
        self.ollama_model = "llama3.2:latest" if self.use_local else None
        
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Successfully initialized OpenAI client")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

        if self.use_local:
            logger.info("本地環境已就緒，使用 Ollama 模型生成對話")
        else:
            logger.info("本地環境不可用，將使用 OpenAI 雲端生成對話")

    async def generate(self, topic: str, context: str = None, target_duration_minutes: int = 8) -> dict:
        """
        生成對話內容

        Args:
            topic (str): 對話的主題
            context (str, optional): 額外的上下文信息. Defaults to None.
            target_duration_minutes (int, optional): 目標對話的時長 (分鐘). Defaults to 8.

        Returns:
            dict: 包含生成對話內容的字典
        """
        if not topic:
            raise ValueError("Topic cannot be empty")

        try:
            if self.use_local:
                logger.info("使用本地 Ollama 生成對話")
                return self._generate_with_ollama(topic, context, target_duration_minutes)
            else:
                logger.info("使用 OpenAI 生成對話")
                return await self._generate_with_openai(topic, context, target_duration_minutes)
        except Exception as e:
            logger.error(f"對話生成失敗: {e}")
            raise

    def _generate_with_ollama(self, topic: str, context: str, target_duration_minutes: int) -> dict:
        """
        使用本地 Ollama 模型生成對話

        Args:
            topic (str): 對話主題
            context (str): 上下文信息
            target_duration_minutes (int): 目標對話時長

        Returns:
            dict: 生成的對話內容
        """
        try:
            system_prompt = self._get_system_prompt(context)
            prompt = f"""{system_prompt}
請基於主題「{topic}」創建對話，時長約為 {target_duration_minutes} 分鐘。
請確保輸出格式為以下 JSON 格式：

{{ 
  "dialogue": [ 
    {{ "id": 1, "User": "M", "text": "..." }},
    {{ "id": 2, "User": "F", "text": "..." }}
  ] 
}}
"""
            logger.debug(f"Ollama 提示語: {prompt}")
            response = ollama.chat(model=self.ollama_model, messages=[{'role': 'user', 'content': prompt}])
            logger.info("Ollama 返回結果成功")
            return self._safe_parse_json(response['message']['content'])
        except Exception as e:
            logger.error(f"Ollama 生成失敗: {e}")
            raise

    async def _generate_with_openai(self, topic: str, context: str, target_duration_minutes: int) -> dict:
        """
        使用 OpenAI API 生成對話

        Args:
            topic (str): 對話主題
            context (str): 上下文信息
            target_duration_minutes (int): 目標對話時長

        Returns:
            dict: 生成的對話內容
        """
        if not hasattr(self, 'client'):
            raise RuntimeError("OpenAI client not properly initialized")

        try:
            system_prompt = self._get_system_prompt(context)
            dialogue = []
            total_duration = 0  # 總時長（秒）
            avg_time_per_round = 45  # 每輪對話的平均時長（秒）

            while total_duration < target_duration_minutes * 60:
                response = self._create_chat_completion(system_prompt, topic, len(dialogue))
                logger.debug(f"OpenAI 返回數據: {response}")
                new_dialogue = self._safe_parse_json(response.choices[0].message.content)

                if not new_dialogue:
                    logger.warning("OpenAI 生成內容無效，跳過本輪")
                    continue

                dialogue.extend(new_dialogue)
                total_duration += len(new_dialogue) * avg_time_per_round
                dialogue = self._truncate_dialogue(dialogue)

            logger.info(f"OpenAI 對話生成成功，共生成 {len(dialogue)} 條")
            return {"dialogue": dialogue}
        except Exception as e:
            logger.error(f"OpenAI 生成失敗: {e}")
            raise

    def _create_chat_completion(self, system_prompt: str, topic: str, previous_rounds: int = 0):
        """
        使用 OpenAI API 創建 Chat Completion

        Args:
            system_prompt (str): 系統提示
            topic (str): 對話主題
            previous_rounds (int, optional): 當前生成輪數. Defaults to 0.

        Returns:
            object: OpenAI API 回應
        """
        try:
            return self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"請基於主題「{topic}」創建第 {previous_rounds + 1} 輪對話。"}
                ],
                temperature=0.7,
                max_tokens=OPENAI_API_MAX_TOKENS
            )
        except Exception as e:
            logger.error(f"OpenAI API 請求失敗: {e}")
            raise

    def _get_system_prompt(self, context: str = None) -> str:
        """
        構造系統提示

        Args:
            context (str, optional): 額外上下文信息. Defaults to None.

        Returns:
            str: 系統提示
        """
        base_prompt = """您是一個專業的 Podcast 製作人,負責創建男女對話的腳本。請遵循以下規則:

1. 創建兩個角色的對話：男性（M）和女性（F）
2. 每句對話以"M:"或"F:"開頭
3. 每段對話保持在40-60個字之間
4. 使用輕鬆、自然的口語化表達
5. 如有專業話題,用簡單易懂的方式解釋
6. 對話要生動有趣,富有互動性
7. 每輪至少生成10個來回的對話

輸出格式為JSON:
{
  "dialogue": [
    {"id": 1, "User": "M", "text": "..."},
    {"id": 2, "User": "F", "text": "..."}
  ]
}"""
        if context:
            base_prompt += f"\n\n請參考以下資訊作為對話內容的依據:\n{context}"
        logger.debug(f"生成的系統提示: {base_prompt}")
        return base_prompt

    def _safe_parse_json(self, content: str) -> list:
        """
        安全解析 JSON

        Args:
            content (str): 要解析的內容

        Returns:
            list: 解析後的 JSON 結果
        """
        try:
            parsed = json.loads(content)
            if "dialogue" in parsed:
                logger.debug(f"成功解析 JSON，對話條數: {len(parsed['dialogue'])}")
                return parsed["dialogue"]
            else:
                logger.warning("生成的內容不包含 'dialogue'")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析錯誤: {e}，生成內容為:\n{content}")
            return self._extract_dialogue_from_text(content)

    def _extract_dialogue_from_text(self, content: str) -> list:
        """
        從純文本中提取對話數據

        Args:
            content (str): 純文本內容

        Returns:
            list: 提取後的對話數據
        """
        dialogue = []
        lines = content.splitlines()
        dialogue_id = 1
        logger.warning("嘗試從純文本中提取對話")
        for line in lines:
            if line.startswith("M：") or line.startswith("W："):
                user = "M" if line.startswith("M：") else "F"
                text = line[2:].strip()  # 去掉開頭標記
                dialogue.append({"id": dialogue_id, "User": user, "text": text})
                dialogue_id += 1
        logger.info(f"成功從純文本提取 {len(dialogue)} 條對話")
        return dialogue

    def _truncate_dialogue(self, dialogue: list) -> list:
        """
        截斷對話以符合 OpenAI API 的最大 token 限制

        Args:
            dialogue (list): 生成的對話列表

        Returns:
            list: 截斷後的對話列表
        """
        total_tokens = sum(len(entry["text"].split()) for entry in dialogue)
        if total_tokens > OPENAI_API_MAX_TOKENS:
            logger.warning(f"對話內容超過最大 token 限制 ({OPENAI_API_MAX_TOKENS})，進行截斷")
            truncated_dialogue = []
            current_tokens = 0
            for entry in dialogue:
                entry_tokens = len(entry["text"].split())
                if current_tokens + entry_tokens <= OPENAI_API_MAX_TOKENS:
                    truncated_dialogue.append(entry)
                    current_tokens += entry_tokens
                else:
                    break
            logger.info(f"截斷後的對話條數: {len(truncated_dialogue)}")
            return truncated_dialogue
        return dialogue