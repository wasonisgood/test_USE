# modules/survey/generator.py
import json
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from config.settings import OPENAI_API_KEY, GPT_MODEL
import uuid

logger = logging.getLogger(__name__)

class SurveyGenerator:
    def __init__(self):
        try:
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Successfully initialized OpenAI client for survey generation")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    async def generate_survey(self, topic: str, survey_id: str) -> Dict:
        """
        根據主題生成調查問卷

        Args:
            topic (str): 問卷主題
            survey_id (str): 唯一問卷ID

        Returns:
            Dict: 包含問卷問題的JSON結構
        """
        try:
            system_prompt = """
            您是一位專業的問卷設計專家。請根據給定主題設計一份簡短的問卷，用於了解聽眾對該主題的認知程度和興趣。

            輸出必須完全符合以下JSON格式：
            {
                "title": "問卷標題",
                "description": "問卷描述",
                "sections": [
                    {
                        "section_id": "section_1",
                        "title": "段落標題",
                        "description": "段落描述",
                        "questions": [
                            {
                                "question_id": "q1",
                                "type": "single_choice", // 可選值: single_choice, multiple_choice, rating, text
                                "required": true,
                                "title": "問題標題",
                                "description": "問題描述（可選）",
                                "options": [ // 僅對 single_choice 和 multiple_choice 有效
                                    {
                                        "option_id": "opt1",
                                        "label": "選項文字",
                                        "value": "選項值"
                                    }
                                ],
                                "validation": { // 根據問題類型設置驗證規則
                                    "min": 0, // 用於 rating 類型
                                    "max": 5, // 用於 rating 類型
                                    "min_select": 1, // 用於 multiple_choice 類型
                                    "max_select": 3, // 用於 multiple_choice 類型
                                    "min_length": 10, // 用於 text 類型
                                    "max_length": 500 // 用於 text 類型
                                }
                            }
                        ]
                    }
                ],
                "settings": {
                    "allow_skip": false,
                    "show_progress": true,
                    "shuffle_questions": false
                }
            }

            問卷必須包含以下四個部分：
            1. 基礎認知評估（單選題）
            - 對主題的熟悉程度
            - 相關經驗
            - 已有知識水平

            2. 興趣方向（多選題）
            - 感興趣的具體面向
            - 希望深入了解的方面
            - 應用場景偏好

            3. 學習目標（評分題，1-5分）
            - 期望達到的理解深度
            - 實際應用意願
            - 時間投入意願

            4. 個性化需求（開放問答）
            - 特定困惑或問題
            - 學習偏好
            - 其他建議

            每個問題都必須：
            1. 有清晰的題幹
            2. 明確的答題說明
            3. 合理的選項設計（選擇題）
            4. 適當的驗證規則
            """

            response = await self._create_chat_completion(
                system_prompt=system_prompt,
                user_prompt=f"請為主題「{topic}」設計一份調查問卷，確保完全符合指定的JSON格式。問卷應該專注於了解用戶對「{topic}」這個主題的認知水平、興趣點和學習需求。"
            )

            return self._process_survey_response(response, survey_id)

        except Exception as e:
            logger.error(f"生成問卷失敗: {e}")
            raise

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
    async def generate_program_plan(self, analysis_report: Dict) -> Dict:
        """
        基於分析報告生成節目規劃

        Args:
            analysis_report (Dict): 聽眾分析報告

        Returns:
            Dict: 節目規劃
        """
        try:
            plan_id = str(uuid.uuid4())  # 生成唯一的 plan_id
            analysis_id = analysis_report.get("analysis_id")  # 获取 analysis_id
            system_prompt = """您是一位專業的廣播節目策劃。請根據聽眾分析報告，設計一份完整的節目規劃。規劃必須完全符合以下JSON格式：
            {
                "created_at": "規劃時間戳",
                "program_info": {
                    "title": "節目標題",
                    "duration": 30, // 預計時長（分鐘）
                    "target_audience": "目標受眾描述",
                    "learning_outcomes": ["預期學習成果1", "成果2"]
                },
                "structure": {
                    "sections": [
                        {
                            "section_id": "section_1",
                            "title": "段落標題",
                            "duration": 8, // 分鐘
                            "type": "introduction/main/conclusion",
                            "content": {
                                "topics": ["要點1", "要點2"],
                                "depth": "內容深度",
                                "key_concepts": ["核心概念1", "概念2"],
                                "examples": ["案例1", "案例2"]
                            },
                            "interaction": {
                                "type": "問答/討論/實例分析",
                                "questions": ["互動問題1", "問題2"],
                                "activities": ["活動設計1", "活動2"]
                            }
                        }
                    ]
                },
                "resources": {
                    "required_materials": ["需要準備的資料1", "資料2"],
                    "supplementary_content": ["補充內容1", "內容2"],
                    "references": ["參考資料1", "資料2"]
                },
                "presentation_guidelines": {
                    "tone": "表達語氣",
                    "pace": "節奏控制",
                    "emphasis_points": ["需要強調的點1", "重點2"],
                    "vocabulary_level": "用詞難度建議"
                }
            }
            """

            response = await self._create_chat_completion(
                system_prompt=system_prompt,
                user_prompt=f"請根據以下分析報告生成節目規劃：{json.dumps(analysis_report, ensure_ascii=False)}"
            )

            return self._process_plan_response(response, plan_id, analysis_id)

        except Exception as e:
            logger.error(f"生成節目規劃失敗: {e}")
            raise
    async def _create_chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        """建立 OpenAI API 請求"""
        try:
            response = self.client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}  # 確保輸出為JSON格式
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API 請求失敗: {e}")
            raise

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
            # 確保使用外部傳入的唯一ID
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

            # 确保将 survey_id 传递给 _process_analysis_response
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



    def _process_plan_response(self, response: str, plan_id: str, analysis_id: str) -> Dict:
        """處理節目規劃回應"""
        try:
            plan_data = json.loads(response)
            # 确保使用生成的 plan_id 和传入的 analysis_id
            plan_data["plan_id"] = plan_id
            plan_data["analysis_id"] = analysis_id
            return plan_data
        except json.JSONDecodeError as e:
            logger.error(f"解析節目規劃失敗: {e}")
            raise
