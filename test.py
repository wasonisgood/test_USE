import asyncio
from audio.generator import AudioGenerator

async def send_callback(entry, audio_info):
    print(f"Generated audio: ID={entry['id']}, File={audio_info['file']}")

dialogue = {
    "dialogue": [
        {"id": 1, "User": "M", "text": "你好，這是第一段對話。"},
        {"id": 2, "User": "F", "text": "你好，這是回應你的第一段對話。"}
    ]
}

async def test_dialogue_audio_generation():
    generator = AudioGenerator()
    await generator.generate_dialogue_audio(dialogue, send_callback)

asyncio.run(test_dialogue_audio_generation())
