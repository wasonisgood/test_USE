# core/websocket.py

import json
import logging
import asyncio
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from websockets.server import WebSocketServerProtocol
from modules.dialogue.generator import DialogueGenerator
from modules.audio.generator import AudioGenerator
from modules.rag.processor import RAGProcessor
from modules.crawler.google import GoogleCrawler
from modules.utils.file_handler import FileHandler
from modules.survey.generator import SurveyGenerator

logger = logging.getLogger(__name__)

class WebSocketHandler:
    def __init__(self):
        """
        初始化 WebSocket 處理器，設置所有需要的組件
        """
        try:
            self.dialogue_generator = DialogueGenerator()
            self.audio_generator = AudioGenerator()
            self.rag_processor = RAGProcessor()
            self.google_crawler = GoogleCrawler()
            self.file_handler = FileHandler()
            self.survey_generator = SurveyGenerator()
            
            # 儲存狀態的字典
            self.active_documents = {}
            self.active_surveys = {}
            
            logger.info("WebSocket handler initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket handler: {e}")
            raise

    async def handle_connection(self, websocket: WebSocketServerProtocol):
        """
        處理 WebSocket 連接
        """
        client_id = id(websocket)
        logger.info(f"新的 WebSocket 連接已建立 (ID: {client_id})")

        try:
            async for message in websocket:
                try:
                    response = await self.process_message(message)
                    await self.send_response(websocket, response)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析錯誤 (ID: {client_id}): {e}")
                    await self.send_error(websocket, "無效的 JSON 格式")
                except Exception as e:
                    logger.error(f"處理消息時發生錯誤 (ID: {client_id}): {e}")
                    await self.send_error(websocket, str(e))
        except Exception as e:
            logger.error(f"WebSocket 處理過程中出錯 (ID: {client_id}): {e}")
        finally:
            if self.google_crawler:
                await self.google_crawler.close()
            logger.info(f"WebSocket 連接已關閉 (ID: {client_id})")

    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        處理接收到的消息，根據消息類型調用相應的處理函數
        """
        try:
            data = json.loads(message)
            message_type = data.get("type")

            handlers = {
                "dialogue": self.handle_dialogue_request,
                "file_process": self.handle_file_process,
                "rag_query": self.handle_rag_query,
                "search": self.handle_search_request,
                "file_list": self.handle_file_list_request,
                "survey_generate": self.handle_survey_generate,
                "survey_submit": self.handle_survey_submit,
                "program_plan": self.handle_program_plan_request,
            }

            handler = handlers.get(message_type)
            if handler:
                logger.info(f"Processing message type: {message_type}")
                return await handler(data)
            else:
                logger.warning(f"未知的請求類型: {message_type}")
                return {"error": "未知的請求類型"}

        except Exception as e:
            logger.error(f"處理消息時發生錯誤: {e}")
            return {"error": str(e)}

    async def handle_dialogue_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理對話生成請求
        """
        try:
            topic = data["topic"]
            use_context = data.get("use_context", True)
            survey_id = data.get("survey_id")
            file_id = data.get("file_id")

            logger.info(f"Generating dialogue for topic: {topic}")

            # 獲取完整上下文
            context = await self._gather_context(topic, survey_id, file_id, use_context)

            # 生成對話
            dialogue_json = await self.dialogue_generator.generate(topic, context)

            return {
                "status": "success",
                "dialogue": dialogue_json
            }

        except Exception as e:
            logger.error(f"處理對話請求失敗: {e}")
            return {"error": str(e)}

    async def handle_survey_generate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理問卷生成請求
        """
        try:
            topic = data.get("topic")
            survey_id = data.get("survey_id")  # 從前端接收 survey_id
            if not topic or not survey_id:
                raise ValueError("主題和問卷 ID 不能為空")

            logger.info(f"Generating survey for topic: {topic}, ID: {survey_id}")
            survey = await self.survey_generator.generate_survey(topic, survey_id)

            self.active_surveys[survey_id] = {
                "topic": topic,
                "survey": survey,
                "responses": None,
                "analysis": None,
                "plan": None,
                "created_at": str(datetime.now())
            }

            return {
                "type": "survey_generated",
                "status": "success",
                "survey_id": survey_id,
                "survey": survey
            }
        except Exception as e:
            logger.error(f"生成問卷失敗: {e}")
            return {"error": str(e)}

    async def handle_survey_submit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理問卷提交
        """
        try:
            survey_id = data["survey_id"]
            responses = data["responses"]
            if survey_id not in self.active_surveys:
                return {"error": "找不到對應的問卷"}

            logger.info(f"Processing survey submission for survey ID: {survey_id}")
            self.active_surveys[survey_id]["responses"] = responses
            analysis = await self.survey_generator.process_responses(responses, survey_id)
            self.active_surveys[survey_id]["analysis"] = analysis
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"處理問卷提交失敗: {e}")
            return {"error": str(e)}


    def _process_survey_response(self, response: str, survey_id: str) -> Dict:
        """
        處理問卷生成回應

        Args:
            response (str): OpenAI API 返回的 JSON 字符串
            survey_id (str): 唯一問卷ID

        Returns:
            Dict: 包含問卷問題的字典
        """
        try:
            survey_data = json.loads(response)
            # 确保使用外部传入的唯一ID
            survey_data["survey_id"] = survey_id
            return survey_data
        except json.JSONDecodeError as e:
            logger.error(f"解析問卷生成結果失敗: {e}")
            raise

    async def process_responses(self, survey_responses: Dict, survey_id: str) -> Dict:
        """
        處理問卷回答並生成聽眾分析報告

        Args:
            survey_responses (Dict): 問卷回答
            survey_id (str): 對應的問卷ID

        Returns:
            Dict: 聽眾分析報告
        """
        try:
            analysis_id = str(uuid.uuid4())  # 生成唯一的 analysis_id
            system_prompt = """您是一位專業的數據分析師。請分析問卷回答，生成一份聽眾分析報告。報告必須完全符合以下JSON格式：
            {
                "created_at": "分析時間戳",
                "overview": {
                    "knowledge_level": {
                        "level": "初級/中級/高級",
                        "score": 0.75, 
                        "description": "整體認知水平描述"
                    },
                    "interest_areas": [
                        {
                            "area": "興趣領域",
                            "priority": 1, 
                            "score": 0.85 
                        }
                    ],
                    "learning_objectives": {
                        "depth": "淺度/中度/深度",
                        "focus_areas": ["重點關注領域1", "重點關注領域2"],
                        "time_commitment": "預期投入時間描述"
                    }
                },
                "recommendations": {
                    "content_level": "建議的內容深度",
                    "key_points": ["需要著重講解的要點1", "要點2"],
                    "approach": "建議的講解方式",
                    "interactive_elements": ["建議的互動環節1", "互動環節2"],
                    "supplementary_materials": ["建議的補充資料1", "補充資料2"]
                },
                "personalization": {
                    "pain_points": ["特別需要解決的問題1", "問題2"],
                    "preferred_learning_style": "偏好的學習方式",
                    "special_requirements": ["特殊需求1", "需求2"]
                }
            }
            """

            response = await self._create_chat_completion(
                system_prompt=system_prompt,
                user_prompt=f"請分析以下問卷回答並生成分析報告：{json.dumps(survey_responses, ensure_ascii=False)}"
            )

            return self._process_analysis_response(response, analysis_id, survey_id)

        except Exception as e:
            logger.error(f"處理問卷回答失敗: {e}")
            raise

    def _process_analysis_response(self, response: str, analysis_id: str, survey_id: str) -> Dict:
        """處理分析報告回應"""
        try:
            analysis_data = json.loads(response)
            # 确保使用生成的 analysis_id 和传入的 survey_id
            analysis_data["analysis_id"] = analysis_id
            analysis_data["survey_id"] = survey_id
            return analysis_data
        except json.JSONDecodeError as e:
            logger.error(f"解析分析報告失敗: {e}")
            raise


    async def handle_program_plan_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理節目規劃請求
        """
        try:
            survey_id = data["survey_id"]
            if survey_id not in self.active_surveys:
                return {"error": "找不到對應的問卷"}

            survey_data = self.active_surveys[survey_id]
            if not survey_data["analysis"]:
                return {"error": "尚未完成問卷分析"}

            logger.info(f"Generating program plan for survey ID: {survey_id}")
            plan = await self.survey_generator.generate_program_plan(survey_data["analysis"])
            self.active_surveys[survey_id]["plan"] = plan
            return {
                "status": "success",
                "plan": plan
            }
        except Exception as e:
            logger.error(f"生成節目規劃失敗: {e}")
            return {"error": str(e)}

    async def handle_file_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理文件處理請求
        """
        try:
            file_path = data["file_path"]
            if not os.path.exists(file_path):
                return {"error": "文件不存在"}

            logger.info(f"Processing file: {file_path}")

            # 處理文件並生成上下文
            document_content = await self.rag_processor.process_document(
                file_path,
                os.path.basename(file_path)
            )

            # 儲存文件信息
            self.active_documents[file_path] = {
                "path": file_path,
                "context": document_content,
                "processed_at": str(datetime.now())
            }

            return {
                "status": "success",
                "file_id": file_path,
                "message": "文件處理完成"
            }

        except Exception as e:
            logger.error(f"處理文件失敗: {e}")
            return {"error": str(e)}

    async def handle_rag_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理 RAG 查詢請求
        """
        try:
            query = data["query"]
            file_id = data.get("file_id")

            if file_id and file_id not in self.active_documents:
                return {"error": "找不到指定的文件"}

            logger.info(f"Processing RAG query: {query}")

            context = await self.rag_processor.get_relevant_context(query)
            return {
                "status": "success",
                "context": context
            }

        except Exception as e:
            logger.error(f"處理 RAG 查詢失敗: {e}")
            return {"error": str(e)}

    async def handle_search_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理搜索請求
        """
        try:
            query = data["query"]
            logger.info(f"Processing search request: {query}")

            results = await self.google_crawler.search(query)
            return {
                "status": "success",
                "results": results
            }

        except Exception as e:
            logger.error(f"處理搜索請求失敗: {e}")
            return {"error": str(e)}

    async def handle_file_list_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理文件列表請求
        """
        try:
            logger.info("Retrieving file list")
            files = self.file_handler.list_files()
            return {
                "status": "success",
                "files": files
            }

        except Exception as e:
            logger.error(f"獲取文件列表失敗: {e}")
            return {"error": str(e)}

    async def _gather_context(self, topic: str, survey_id: str = None, file_id: str = None, use_context: bool = True) -> Optional[str]:
        """
        收集所有可用的上下文
        """
        if not use_context:
            return None

        contexts = []
        
        # 獲取問卷相關上下文
        if survey_id and survey_id in self.active_surveys:
            survey_data = self.active_surveys[survey_id]
            if survey_data.get("plan"):
                contexts.append(f"節目規劃：\n{json.dumps(survey_data['plan'], ensure_ascii=False)}")

        # 獲取文件上下文
        if file_id and file_id in self.active_documents:
            file_context = self.active_documents[file_id].get("context")
            if file_context:
                contexts.append(f"文件內容：\n{file_context}")

        # 獲取搜索上下文
        search_context = await self.get_enhanced_context(topic)
        if search_context:
            contexts.append(f"搜索內容：\n{search_context}")

        return "\n\n".join(contexts) if contexts else None

    async def get_enhanced_context(self, topic: str) -> Optional[str]:
        """
        獲取增強的上下文信息
        """
        try:
            contexts = []

            # 從 RAG 獲取上下文
            rag_context = await self.rag_processor.get_relevant_context(topic)
            if rag_context:
                contexts.append(rag_context)

            # 從網絡搜索獲取上下文
            search_results = await self.google_crawler.search(topic)
            if search_results:
                contexts.append(search_results)

            return "\n\n".join(contexts) if contexts else None

        except Exception as e:
            logger.error(f"獲取增強上下文失敗: {e}")
            return None

    async def send_response(self, websocket: WebSocketServerProtocol, response: Dict[str, Any]):
        """
        發送響應消息
        """
        try:
            if response.get("status") == "success" and "dialogue" in response:
                async def send_audio_entry(entry, audio_info):
                    """發送單條對話與音頻信息"""
                    await websocket.send(json.dumps({
                        "status": "section_ready",
                        "id": entry["id"],
                        "user": entry["User"],
                        "text": entry["text"],
                        "audio_file": audio_info["file"]
                    }))
                    await asyncio.sleep(0.1)  # 防止消息發送過快

                # 實時生成並發送
                await self.audio_generator.generate_dialogue_audio(
                    dialogue=response["dialogue"],
                    send_callback=send_audio_entry
                )

                # 完成所有發送後，發送完成狀態
                await websocket.send(json.dumps({"status": "complete"}))
            else:
                # 對於其他響應類型直接發送
                await websocket.send(json.dumps(response))

        except Exception as e:
            logger.error(f"發送響應失敗: {e}")
            await self.send_error(websocket, str(e))

    async def send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """
        發送錯誤消息
        """
        try:
            await websocket.send(json.dumps({
                "status": "error",
                "error": error_message
            }))
        except Exception as e:
            logger.error(f"發送錯誤消息失敗: {e}")
