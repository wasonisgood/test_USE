# modules/rag/embeddings.py

import numpy as np
from typing import List, Dict, Any
import json
import logging
from pathlib import Path
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
from config.settings import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    EMBEDDINGS_DIR
)

logger = logging.getLogger(__name__)

class EmbeddingsManager:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.embeddings_cache = {}
        self.cache_file = EMBEDDINGS_DIR / "embeddings_cache.json"
        self._load_cache()

    def _load_cache(self):
        """加載嵌入向量緩存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    # 將字符串列表轉換回 numpy 數組
                    self.embeddings_cache = {
                        k: np.array(v) for k, v in cache_data.items()
                    }
                logger.info(f"已加載 {len(self.embeddings_cache)} 個嵌入向量")
            else:
                logger.info("未找到緩存文件，創建新的緩存")
        except Exception as e:
            logger.error(f"加載嵌入向量緩存失敗: {e}")
            self.embeddings_cache = {}

    def _save_cache(self):
        """保存嵌入向量到緩存"""
        try:
            # 將 numpy 數組轉換為列表以便 JSON 序列化
            cache_data = {
                k: v.tolist() for k, v in self.embeddings_cache.items()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f)
            logger.info("嵌入向量緩存已保存")
        except Exception as e:
            logger.error(f"保存嵌入向量緩存失敗: {e}")

    async def get_embedding(self, text: str) -> np.ndarray:
        """獲取文本的嵌入向量"""
        try:
            # 檢查緩存
            if text in self.embeddings_cache:
                return self.embeddings_cache[text]

            # 使用 OpenAI API 生成嵌入向量
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            
            embedding = np.array(response.data[0].embedding)
            
            # 保存到緩存
            self.embeddings_cache[text] = embedding
            self._save_cache()
            
            return embedding

        except Exception as e:
            logger.error(f"生成嵌入向量失敗: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> Dict[str, np.ndarray]:
        """批量獲取多個文本的嵌入向量"""
        embeddings = {}
        for text in texts:
            try:
                embedding = await self.get_embedding(text)
                embeddings[text] = embedding
            except Exception as e:
                logger.error(f"處理文本嵌入失敗: {text[:50]}... - {e}")
                continue
        return embeddings

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """計算兩個嵌入向量之間的餘弦相似度"""
        # 重塑向量以符合 sklearn 的要求
        embedding1_reshaped = embedding1.reshape(1, -1)
        embedding2_reshaped = embedding2.reshape(1, -1)
        
        # 使用 sklearn 計算餘弦相似度
        similarity = cosine_similarity(embedding1_reshaped, embedding2_reshaped)[0][0]
        return float(similarity)

    async def find_most_similar(
        self, 
        query: str, 
        candidates: List[str], 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """找出與查詢最相似的文本"""
        try:
            query_embedding = await self.get_embedding(query)
            query_embedding_reshaped = query_embedding.reshape(1, -1)
            
            similarities = []
            for text in candidates:
                try:
                    text_embedding = await self.get_embedding(text)
                    text_embedding_reshaped = text_embedding.reshape(1, -1)
                    
                    similarity = cosine_similarity(
                        query_embedding_reshaped, 
                        text_embedding_reshaped
                    )[0][0]
                    
                    similarities.append({
                        'text': text,
                        'similarity': float(similarity)
                    })
                except Exception as e:
                    logger.error(f"計算相似度失敗: {e}")
                    continue

            # 按相似度排序
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]

        except Exception as e:
            logger.error(f"查找相似文本失敗: {e}")
            return []

    def cleanup_cache(self, max_size: int = 1000):
        """清理緩存，保留最近使用的向量"""
        if len(self.embeddings_cache) > max_size:
            # 簡單的緩存清理策略：保留最新的 max_size 個項目
            items = list(self.embeddings_cache.items())
            self.embeddings_cache = dict(items[-max_size:])
            self._save_cache()
            logger.info(f"清理緩存，保留 {max_size} 個向量")