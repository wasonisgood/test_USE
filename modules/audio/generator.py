import logging
from pathlib import Path
from openai import OpenAI
from config.settings import OPENAI_API_KEY, TTS_MODEL, AUDIO_DIR

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    async def generate(self, text: str, voice_type: str, file_name: str) -> Path:
        """
        生成音频文件

        Args:
            text: 要转换的文本
            voice_type: 语音类型 ('alloy' 或 'onyx')
            file_name: 保存的文件名

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

            logger.debug(f"音频生成成功: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"生成音频失败: {e}")
            raise

    async def generate_dialogue_audio(self, dialogue: dict, send_callback: callable) -> list:
        """
        为整个对话生成音频并逐条发送。

        Args:
            dialogue: 对话内容字典
            send_callback: 用于实时发送的回调函数

        Returns:
            list: 所有生成音频文件的信息
        """
        audio_files = []
        for entry in dialogue["dialogue"]:
            try:
                filename = f"voice{entry['id']}.mp3"
                voice_type = 'onyx' if entry["User"] == "M" else 'alloy'

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
