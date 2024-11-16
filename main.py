import logging
from core.server import PodcastServer

if __name__ == "__main__":
    try:
        server = PodcastServer()
        server.start()
    except Exception as e:
        logging.error(f"服務器運行時發生錯誤: {e}")
        raise