"""
임베딩 생성 모듈 - sentence-transformers 사용
"""

from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL


class EmbeddingModel:
    """sentence-transformers 모델 래퍼 (싱글톤 패턴)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.model = SentenceTransformer(EMBEDDING_MODEL)
        return cls._instance


def generate_embedding(text: str, model: EmbeddingModel) -> list:
    """
    텍스트 → 임베딩 벡터 (list[float])
    빈 문자열도 안전하게 처리
    """
    if not text:
        text = "알 수 없음"
    vec = model.model.encode(text, normalize_embeddings=True)
    return vec.tolist()
