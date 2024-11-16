# modules/rag/retriever.py

import logging
from typing import List, Dict, Any, Optional
from .embeddings import EmbeddingsManager
import numpy as np
from pathlib import Path
import json
from datetime import datetime
from config.settings import TOP_K_RESULTS

logger = logging.getLogger(__name__)

class DocumentRetriever:
    def __init__(self):
        self.embeddings_manager = EmbeddingsManager()
        self.document_chunks = {}
        self.chunk_metadata = {}

    def add_document(self, doc_id: str, chunks: List[Dict[str, str]], metadata: Dict[str, Any] = None):
        """添加文檔和其分塊"""
        self.document_chunks[doc_id] = chunks
        self.chunk_metadata[doc_id] = {
            'metadata': metadata or {},
            'added_at': datetime.now().isoformat(),
            'chunk_count': len(chunks)
        }
        logger.info(f"添加文檔 {doc_id}，包含 {len(chunks)} 個分塊")

    async def search(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        threshold: float = 0.7,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """搜索相關文本塊"""
        try:
            all_chunks = []
            for doc_id, chunks in self.document_chunks.items():
                # 如果有過濾條件，檢查文檔是否符合
                if filters and not self._check_filters(doc_id, filters):
                    continue
                all_chunks.extend([
                    {**chunk, 'doc_id': doc_id}
                    for chunk in chunks
                ])

            if not all_chunks:
                logger.warning("沒有找到符合條件的文檔")
                return []

            # 獲取所有候選文本
            candidate_texts = [chunk['text'] for chunk in all_chunks]
            
            # 查找最相似的文本
            similar_results = await self.embeddings_manager.find_most_similar(
                query, candidate_texts, top_k
            )

            # 過濾相似度低於閾值的結果
            filtered_results = [
                result for result in similar_results
                if result['similarity'] >= threshold
            ]

            # 添加元數據
            enriched_results = []
            for result in filtered_results:
                chunk_info = next(
                    chunk for chunk in all_chunks
                    if chunk['text'] == result['text']
                )
                enriched_results.append({
                    **result,
                    'doc_id': chunk_info['doc_id'],
                    'chunk_id': chunk_info.get('id'),
                    'metadata': self.chunk_metadata[chunk_info['doc_id']]
                })

            logger.info(f"查詢 '{query}' 找到 {len(enriched_results)} 個相關結果")
            return enriched_results

        except Exception as e:
            logger.error(f"搜索失敗: {e}")
            return []

    async def get_similar_chunks(
        self,
        chunk_id: str,
        doc_id: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """獲取與指定塊相似的其他塊"""
        try:
            # 獲取目標塊的文本
            target_chunk = next(
                chunk for chunk in self.document_chunks[doc_id]
                if chunk['id'] == chunk_id
            )

            # 收集同一文檔中的其他塊
            other_chunks = [
                chunk for chunk in self.document_chunks[doc_id]
                if chunk['id'] != chunk_id
            ]

            # 查找相似塊
            similar_chunks = await self.embeddings_manager.find_most_similar(
                target_chunk['text'],
                [chunk['text'] for chunk in other_chunks],
                top_k
            )

            return similar_chunks

        except Exception as e:
            logger.error(f"獲取相似塊失敗: {e}")
            return []

    def _check_filters(self, doc_id: str, filters: Dict[str, Any]) -> bool:
        """檢查文檔是否符合過濾條件"""
        try:
            metadata = self.chunk_metadata[doc_id]['metadata']
            
            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    return False
            return True
            
        except Exception as e:
            logger.error(f"檢查過濾條件失敗: {e}")
            return False

    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """獲取文檔信息"""
        try:
            if doc_id not in self.chunk_metadata:
                return None

            return {
                'doc_id': doc_id,
                'metadata': self.chunk_metadata[doc_id],
                'chunk_count': len(self.document_chunks[doc_id])
            }

        except Exception as e:
            logger.error(f"獲取文檔信息失敗: {e}")
            return None

    def remove_document(self, doc_id: str):
        """移除文檔"""
        try:
            self.document_chunks.pop(doc_id, None)
            self.chunk_metadata.pop(doc_id, None)
            logger.info(f"已移除文檔: {doc_id}")
        except Exception as e:
            logger.error(f"移除文檔失敗: {e}")

    async def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """重新排序搜索結果"""
        try:
            # 這裡可以實現更複雜的重排序邏輯
            # 目前簡單地按相似度排序
            return sorted(
                results,
                key=lambda x: x['similarity'],
                reverse=True
            )
        except Exception as e:
            logger.error(f"重新排序結果失敗: {e}")
            return results