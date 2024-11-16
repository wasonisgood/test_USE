# config/settings.py

import os
from pathlib import Path

# 基礎路徑配置
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = BASE_DIR / "static"
AUDIO_DIR = BASE_DIR / "data" / "audio"
LOG_DIR = BASE_DIR / "logs"
EMBEDDINGS_DIR = BASE_DIR / "data" / "embeddings"

# 創建必要的目錄
for dir_path in [STATIC_DIR, AUDIO_DIR, LOG_DIR, EMBEDDINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# 服務器配置
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8888
HTTP_PORT = 8000

# OpenAI 配置
OPENAI_API_KEY = os.getenv("xxx", "")
GPT_MODEL = "gpt-4o-mini"
TTS_MODEL = "tts-1"
EMBEDDING_MODEL = "text-embedding-ada-002"

# RAG 配置
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5

# 爬蟲配置
GOOGLE_SEARCH_LIMIT = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# 音頻配置
AUDIO_CLEANUP_INTERVAL = 3600  # 1小時
AUDIO_MAX_AGE = 3600  # 1小時
AUDIO_CLEANUP_INTERVAL = 3600  # 1 hour
AUDIO_MAX_AGE = 86400  # 1 day

# M3U8 串流相關配置
M3U8_SEGMENT_DURATION = 5  # 5 seconds per segment
M3U8_DIRECTORY = Path("data/m3u8")

# 日誌配置
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = 'DEBUG'
# 對話長度限制
DIALOGUE_MAX_LENGTH = 40
OPENAI_API_MAX_TOKENS = 4096