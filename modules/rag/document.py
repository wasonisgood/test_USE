# modules/rag/document.py

from typing import List, Dict, Any
import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """文檔處理器，用於處理不同類型的文檔"""
    
    @staticmethod
    def process_csv(file_path: Path) -> str:
        """處理 CSV 文件"""
        try:
            df = pd.read_csv(file_path)
            # 將 DataFrame 轉換為文本描述
            text_content = []
            
            # 添加基本信息
            text_content.append(f"這是一個包含 {len(df)} 行和 {len(df.columns)} 列的數據集")
            text_content.append(f"列名包括：{', '.join(df.columns)}")
            
            # 添加數值列的統計信息
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
            for col in numeric_cols:
                stats = df[col].describe()
                text_content.append(f"\n{col} 的統計信息：")
                text_content.append(f"平均值：{stats['mean']:.2f}")
                text_content.append(f"最大值：{stats['max']:.2f}")
                text_content.append(f"最小值：{stats['min']:.2f}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"處理 CSV 文件失敗: {e}")
            raise

    @staticmethod
    def process_txt(file_path: Path) -> str:
        """處理文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"處理文本文件失敗: {e}")
            raise

    @staticmethod
    def process_json(file_path: Path) -> str:
        """處理 JSON 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"處理 JSON 文件失敗: {e}")
            raise

    @classmethod
    def process(cls, file_path: Path) -> str:
        """根據文件類型處理文檔"""
        suffix = file_path.suffix.lower()
        
        processors = {
            '.csv': cls.process_csv,
            '.txt': cls.process_txt,
            '.json': cls.process_json
        }
        
        processor = processors.get(suffix)
        if not processor:
            raise ValueError(f"不支持的文件類型: {suffix}")
            
        return processor(file_path)