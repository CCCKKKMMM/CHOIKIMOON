"""
multivector_embedding.py — 하이브리드 벡터 생성 (448차원)

behavior(256) + genre(128) + demographic(64) 연결
"""
import numpy as np
from behavior_embedding import build_behavior_vector
from genre_embedding import build_genre_vector
from demographic_embedding import build_demographic_vector


def build_hybrid_vector(numeric: dict) -> np.ndarray:
    """
    수치 특징 딕셔너리 → 하이브리드 벡터 (448차원)

    Args:
        numeric: extract_numeric_features() 반환값
    Returns:
        np.ndarray shape=(448,) dtype=float32
    """
    b = build_behavior_vector(numeric)
    g = build_genre_vector(numeric)
    d = build_demographic_vector(numeric)
    return np.concatenate([b, g, d]).astype(np.float32)
