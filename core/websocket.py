import json
import logging
import asyncio
from websockets.server import WebSocketServerProtocol
from modules.dialogue.generator import DialogueGenerator
from modules.audio.generator import AudioGenerator
from modules.rag.processor import RAGProcessor
from modules.crawler.google import GoogleCrawler
from modules.utils.file_handler import FileHandler
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self):
        self.dialogue_generator = DialogueGenerator()
        self.audio_generator = AudioGenerator()
        self.rag_processor = RAGProcessor()
        self.google_crawler = GoogleCrawler()
        self.file_handler = FileHandler()
        self.active_documents = {}  # 存储活跃的文档信息

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """处理 WebSocket 连接"""
        client_id = id(websocket)
        logger.info(f"新的 WebSocket 连接已建立 (ID: {client_id})")

        try:
            async for message in websocket:
                try:
                    response = await self.process_message(message)
                    await self.send_response(websocket, response)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析错误 (ID: {client_id}): {e}")
                    await self.send_error(websocket, "无效的 JSON 格式")
        except Exception as e:
            logger.error(f"WebSocket 处理过程中出错 (ID: {client_id}): {e}")
        finally:
            if self.google_crawler:
                await self.google_crawler.close()

    async def process_message(self, message: str) -> Dict[str, Any]:
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            message_type = data.get("type")

            handlers = {
                "dialogue": self.handle_dialogue_request,
                "file_process": self.handle_file_process,
                "rag_query": self.handle_rag_query,
                "search": self.handle_search_request,
                "file_list": self.handle_file_list_request
            }

            handler = handlers.get(message_type)
            if handler:
                return await handler(data)
            else:
                logger.warning(f"未知的请求类型: {message_type}")
                return {"error": "未知的请求类型"}

        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            return {"error": str(e)}

    async def handle_dialogue_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理对话生成请求"""
        try:
            topic = data["topic"]
            use_context = data.get("use_context", True)
            file_id = data.get("file_id")

            context = None
            if use_context:
                # 获取文件上下文
                if file_id and file_id in self.active_documents:
                    file_context = self.active_documents[file_id].get("context")
                    if file_context:
                        context = file_context

                # 获取网络搜索上下文
                search_context = await self.get_enhanced_context(topic)
                if search_context:
                    context = f"{context}\n\n{search_context}" if context else search_context

            # 生成对话
            dialogue_json = await self.dialogue_generator.generate(topic, context)

            return {
                "status": "success",
                "dialogue": dialogue_json
            }

        except Exception as e:
            logger.error(f"处理对话请求失败: {e}")
            return {"error": str(e)}

    async def handle_file_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文件处理请求"""
        try:
            file_path = Path(data["file_path"])
            if not file_path.exists():
                return {"error": "文件不存在"}

            # 处理文件并生成上下文
            document_content = await self.rag_processor.process_document(
                str(file_path),
                str(file_path.name)
            )

            # 存储文件信息
            self.active_documents[str(file_path.name)] = {
                "path": str(file_path),
                "context": document_content
            }

            return {
                "status": "success",
                "file_id": str(file_path.name),
                "message": "文件处理完成"
            }

        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            return {"error": str(e)}

    async def handle_rag_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 RAG 查询请求"""
        try:
            query = data["query"]
            file_id = data.get("file_id")

            if file_id and file_id not in self.active_documents:
                return {"error": "找不到指定的文件"}

            context = await self.rag_processor.get_relevant_context(query)
            return {
                "status": "success",
                "context": context
            }

        except Exception as e:
            logger.error(f"处理 RAG 查询失败: {e}")
            return {"error": str(e)}

    async def handle_search_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理搜索请求"""
        try:
            query = data["query"]
            results = await self.google_crawler.search(query)
            return {
                "status": "success",
                "results": results
            }

        except Exception as e:
            logger.error(f"处理搜索请求失败: {e}")
            return {"error": str(e)}

    async def handle_file_list_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理文件列表请求"""
        try:
            files = self.file_handler.list_files()
            return {
                "status": "success",
                "files": files
            }

        except Exception as e:
            logger.error(f"获取文件列表失败: {e}")
            return {"error": str(e)}

    async def get_enhanced_context(self, topic: str) -> Optional[str]:
        """获取增强的上下文信息"""
        try:
            contexts = []

            # 从 RAG 获取上下文
            rag_context = await self.rag_processor.get_relevant_context(topic)
            if rag_context:
                contexts.append(rag_context)

            # 从网络搜索获取上下文
            search_results = await self.google_crawler.search(topic)
            if search_results:
                contexts.append(search_results)

            return "\n\n".join(contexts) if contexts else None

        except Exception as e:
            logger.error(f"获取增强上下文失败: {e}")
            return None

    async def send_response(self, websocket: WebSocketServerProtocol, response: Dict[str, Any]):
        """发送响应消息"""
        try:
            if response.get("status") == "success" and "dialogue" in response:
                async def send_audio_entry(entry, audio_info):
                    """发送单条对话与音频信息"""
                    await websocket.send(json.dumps({
                        "status": "section_ready",
                        "id": entry["id"],
                        "user": entry["User"],
                        "text": entry["text"],
                        "audio_file": audio_info["file"]
                    }))
                    await asyncio.sleep(0.1)  # 防止消息发送过快

                # 实时生成并发送
                await self.audio_generator.generate_dialogue_audio(
                    dialogue=response["dialogue"],
                    send_callback=send_audio_entry
                )

                # 完成所有发送后，发送完成状态
                await websocket.send(json.dumps({"status": "complete"}))
            else:
                # 对于其他响应类型直接发送
                await websocket.send(json.dumps(response))

        except Exception as e:
            logger.error(f"发送响应失败: {e}")
            await self.send_error(websocket, str(e))

    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """发送错误消息"""
        try:
            await websocket.send(json.dumps({
                "error": error_message
            }))
        except Exception as e:
            logger.error(f"发送错误消息失败: {e}")
