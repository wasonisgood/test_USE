# modules/rag/processor.py

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from openai import OpenAI
from config.settings import (
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    TOP_K_RESULTS,
    EMBEDDINGS_DIR
)
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class RAGProcessor:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.embeddings_cache = {}
        self.document_chunks = {}
        self._load_cached_embeddings()

    def _load_cached_embeddings(self):
        """加載緩存的嵌入向量"""
        try:
            cache_file = EMBEDDINGS_DIR / "embeddings_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.embeddings_cache = json.load(f)
            logger.info(f"已加載 {len(self.embeddings_cache)} 個緩存嵌入向量")
        except Exception as e:
            logger.error(f"加載嵌入向量緩存失敗: {e}")

    def _save_cached_embeddings(self):
        """保存嵌入向量到緩存"""
        try:
            cache_file = EMBEDDINGS_DIR / "embeddings_cache.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.embeddings_cache, f)
            logger.info("嵌入向量緩存已保存")
        except Exception as e:
            logger.error(f"保存嵌入向量緩存失敗: {e}")

    async def process_document(self, document: str, doc_id: str) -> List[Dict[str, str]]:
        """處理文檔並創建塊"""
        chunks = self._split_text(document)
        self.document_chunks[doc_id] = chunks
        
        # 為每個塊生成嵌入向量
        for chunk in chunks:
            if chunk["text"] not in self.embeddings_cache:
                embedding = await self._get_embedding(chunk["text"])
                self.embeddings_cache[chunk["text"]] = embedding

        self._save_cached_embeddings()
        return chunks

    def _split_text(self, text: str) -> List[Dict[str, str]]:
        """將文本分割成塊"""
        words = text.split()
        chunks = []
        chunk_id = 0
        
        while chunk_id * (CHUNK_SIZE - CHUNK_OVERLAP) < len(words):
            start_idx = chunk_id * (CHUNK_SIZE - CHUNK_OVERLAP)
            end_idx = min(start_idx + CHUNK_SIZE, len(words))
            chunk_text = ' '.join(words[start_idx:end_idx])
            chunks.append({
                "id": str(chunk_id),
                "text": chunk_text
            })
            chunk_id += 1
        
        return chunks

    async def _get_embedding(self, text: str) -> List[float]:
        """獲取文本的嵌入向量"""
        try:
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"獲取嵌入向量失敗: {e}")
            raise

    async def search_relevant_chunks(self, query: str, top_k: int = TOP_K_RESULTS) -> List[str]:
        """搜索相關的文本塊"""
        try:
            query_embedding = await self._get_embedding(query)
            similarities = {}
            
            for text, embedding in self.embeddings_cache.items():
                similarity = cosine_similarity(
                    [query_embedding],
                    [embedding]
                )[0][0]
                similarities[text] = similarity
            
            # 排序並返回最相關的塊
            sorted_chunks = sorted(
                similarities.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [chunk[0] for chunk in sorted_chunks[:top_k]]
            
        except Exception as e:
            logger.error(f"搜索相關塊失敗: {e}")
            return []

    async def get_relevant_context(self, query: str) -> Optional[str]:
        """獲取相關上下文"""
        try:
            relevant_chunks = await self.search_relevant_chunks(query)
            if not relevant_chunks:
                return None
                
            context = "\n\n".join(relevant_chunks)
            return f"基於現有資料的相關信息：\n\n{context}"
            
        except Exception as e:
            logger.error(f"獲取相關上下文失敗: {e}")
            return None

