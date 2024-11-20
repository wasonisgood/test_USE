import logging
import os
import signal
import sys
from core.server import PodcastServer
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ReloadHandler(FileSystemEventHandler):
    """
    文件變更處理器，當監測到文件變更時重啟服務器
    """
    def __init__(self, server):
        self.server = server

    def on_any_event(self, event):
        if event.src_path.endswith(".py"):
            logging.info(f"檢測到文件變更: {event.src_path}")
            self.restart_server()

    def restart_server(self):
        logging.info("重啟服務器...")
        os.kill(os.getpid(), signal.SIGINT)


def start_with_hot_reload():
    """
    啟動服務器並啟用熱修復功能
    """
    server = PodcastServer()
    observer = Observer()
    event_handler = ReloadHandler(server)
    observer.schedule(event_handler, path=".", recursive=True)
    observer.start()

    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("關閉服務器...")
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    start_with_hot_reload()
