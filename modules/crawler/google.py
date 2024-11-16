# modules/crawler/google.py

import logging
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from config.settings import GOOGLE_SEARCH_LIMIT, USER_AGENT

logger = logging.getLogger(__name__)

class GoogleCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': USER_AGENT
        }
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """確保 session 存在"""
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def close(self):
        """關閉 session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def search(self, query: str) -> str:
        """執行 Google 搜索並返回處理後的結果"""
        try:
            await self._ensure_session()
            search_results = await self._google_search(query)
            
            if not search_results:
                return ""
            
            # 獲取頁面內容
            contents = await asyncio.gather(*[
                self._get_page_content(result["link"]) 
                for result in search_results[:3]  # 只處理前3個結果
            ])
            
            # 組合結果
            processed_results = []
            for result, content in zip(search_results[:3], contents):
                if content:
                    processed_results.append(
                        f"標題: {result['title']}\n"
                        f"摘要: {result['snippet']}\n"
                        f"內容: {content}\n"
                    )
            
            return "\n---\n".join(processed_results)
            
        except Exception as e:
            logger.error(f"搜索失敗: {e}")
            return ""

    async def _google_search(self, query: str) -> List[Dict[str, str]]:
        """執行 Google 搜索"""
        try:
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={GOOGLE_SEARCH_LIMIT}"
            
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    logger.error(f"Google 搜索請求失敗: {response.status}")
                    return []
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                results = []
                for g in soup.find_all('div', class_='g'):
                    title_element = g.find('h3')
                    link_element = g.find('a')
                    snippet_element = g.find('div', class_='VwiC3b')
                    
                    if title_element and link_element and snippet_element:
                        results.append({
                            'title': title_element.text,
                            'link': link_element['href'],
                            'snippet': snippet_element.text
                        })
                
                return results
                
        except Exception as e:
            logger.error(f"執行 Google 搜索失敗: {e}")
            return []

    async def _get_page_content(self, url: str) -> str:
        """獲取網頁內容"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return ""
                    
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 移除不需要的元素
                for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                    element.decompose()
                
                # 獲取主要內容
                content = soup.find('main') or soup.find('article') or soup.find('body')
                if content:
                    # 清理文本
                    text = ' '.join(content.stripped_strings)
                    # 限制長度
                    return text[:1000] + "..." if len(text) > 1000 else text
                    
                return ""
                
        except Exception as e:
            logger.error(f"獲取頁面內容失敗 ({url}): {e}")
            return ""

