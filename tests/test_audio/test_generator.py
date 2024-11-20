import asyncio
from modules.audio.generator import AudioGenerator

async def test_audio_generation():
    """
    測試生成單條音頻文件
    """
    generator = AudioGenerator()
    file_path = await generator.generate("你好，這是一段測試文本。", "zh-TW-YunJheNeural", "test_audio.mp3")
    assert file_path.exists(), "音頻文件未生成"

async def test_dialogue_audio_generation():
    """
    測試為整段對話生成音頻
    """
    async def mock_send_callback(entry, audio_info):
        print(f"Generated audio: ID={entry['id']}, File={audio_info['file']}")

    dialogue = {
        "dialogue": [
            {"id": 1, "User": "M", "text": "你好，這是一段測試文本。"},
            {"id": 2, "User": "F", "text": "你好，這是回應。"}
        ]
    }

    generator = AudioGenerator()
    audio_files = await generator.generate_dialogue_audio(dialogue, mock_send_callback)
    assert len(audio_files) == len(dialogue["dialogue"]), "音頻文件生成數量不匹配"

if __name__ == "__main__":
    asyncio.run(test_audio_generation())
    asyncio.run(test_dialogue_audio_generation())
