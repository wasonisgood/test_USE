import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class OllamaGenerator:
    def __init__(self, model_name: str = "llama3.2:latest"):
        self.model_name = model_name

    def generate(self, prompt: str) -> dict:
        """
        使用 Ollama 生成對話

        Args:
            prompt: 提示文字

        Returns:
            dict: 包含生成內容的字典
        """
        try:
            process = subprocess.run(
                ["ollama", "generate", self.model_name, "--prompt", prompt],
                capture_output=True,
                text=True,
                check=True
            )
            response = process.stdout.strip()
            return json.loads(response)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
            logger.error(f"Ollama 生成失敗: {e}")
            raise
