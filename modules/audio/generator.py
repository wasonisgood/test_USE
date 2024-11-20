import logging
import asyncio
from pathlib import Path
from config.settings import OPENAI_API_KEY, TTS_MODEL, AUDIO_DIR
from modules.ollama.checker import HardwareChecker
from openai import OpenAI
import edge_tts

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        """
        初始化音频生成器，检测本地 TTS 支持
        """
        self.use_local = HardwareChecker.is_local_environment_ready()
        self.client = OpenAI(api_key=OPENAI_API_KEY) if not self.use_local else None

    async def generate(self, text: str, voice_type: str, file_name: str) -> Path:
        """
        生成音频文件

        Args:
            text (str): 要转换的文本
            voice_type (str): 语音类型（如 Edge TTS 的语音名称）
            file_name (str): 保存的文件名

        Returns:
            Path: 生成的音频文件路径
        """
        if self.use_local:
            return await self._generate_with_local(text, voice_type, file_name)
        else:
            return await self._generate_with_openai(text, voice_type, file_name)

    async def _generate_with_local(self, text: str, voice_type: str, file_name: str) -> Path:
        """
        使用本地 Edge TTS 工具生成音频

        Args:
            text (str): 要转换的文本
            voice_type (str): Edge TTS 的语音名称
            file_name (str): 保存的文件名

        Returns:
            Path: 生成的音频文件路径
        """
        try:
            file_path = AUDIO_DIR / file_name
            # 使用 Edge TTS 生成音频
            communicate = edge_tts.Communicate(text, voice_type)
            await communicate.save(str(file_path))
            logger.info(f"本地音频生成成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"本地 TTS 工具生成音频失败: {e}")
            raise

    async def _generate_with_openai(self, text: str, voice_type: str, file_name: str) -> Path:
        """
        使用 OpenAI API 生成音频

        Args:
            text (str): 要转换的文本
            voice_type (str): OpenAI API 的语音类型
            file_name (str): 保存的文件名

        Returns:
            Path: 生成的音频文件路径
        """
        try:
            file_path = AUDIO_DIR / file_name
            response = self.client.audio.speech.create(
                model=TTS_MODEL,
                voice=voice_type,
                input=text
            )
            response.stream_to_file(str(file_path))
            logger.info(f"云端音频生成成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"生成音频失败: {e}")
            raise

    async def generate_dialogue_audio(self, dialogue: dict, send_callback: callable) -> list:
        """
        为整个对话生成音频并逐条发送

        Args:
            dialogue (dict): 对话内容字典
            send_callback (callable): 用于实时发送的回调函数

        Returns:
            list: 所有生成音频文件的信息
        """
        audio_files = []
        for entry in dialogue["dialogue"]:
            try:
                filename = f"voice{entry['id']}.mp3"
                voice_type = (
                    "zh-TW-YunJheNeural" if entry["User"] == "M" else "zh-TW-HsiaoChenNeural"
                )

                # 音频生成
                file_path = await self.generate(
                    text=entry["text"],
                    voice_type=voice_type,
                    file_name=filename
                )

                # 存储音频信息
                audio_info = {
                    "id": entry["id"],
                    "file": f"/audio/{filename}",
                    "user": entry["User"]
                }
                audio_files.append(audio_info)

                # 调用回调函数，实时发送
                if send_callback:
                    await send_callback(entry, audio_info)

            except Exception as e:
                logger.error(f"处理对话音频失败 - ID {entry['id']}: {e}")
                raise

        return audio_files
