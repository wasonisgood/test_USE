# modules/crawler/processor.py

import logging
from typing import Dict, Any
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class ContentProcessor:
    """網頁內容處理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        # 移除多餘的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 移除 HTML 實體
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        return text.strip()

    @staticmethod
    def extract_main_content(html: str) -> str:
        """提取主要內容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 移除不需要的元素
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # 嘗試找到主要內容區域
            main_content = None
            for selector in ['main', 'article', '.content', '.main', '#content', '#main']:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if not main_content:
                main_content = soup.find('body')
            
            if main_content:
                text = ' '.join(main_content.stripped_strings)
                return ContentProcessor.clean_text(text)
            
            return ""
            
        except Exception as e:
            logger.error(f"提取主要內容失敗: {e}")
            return ""

    @classmethod
    def process_search_result(cls, result: Dict[str, Any]) -> str:
        """處理搜索結果"""
        try:
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            content = result.get('content', '')
            
            processed_text = (
                f"標題：{cls.clean_text(title)}\n"
                f"摘要：{cls.clean_text(snippet)}\n"
                f"內容：{cls.clean_text(content)}"
            )
            
            return processed_text
            
        except Exception as e:
            logger.error(f"處理搜索結果失敗: {e}")
            return ""