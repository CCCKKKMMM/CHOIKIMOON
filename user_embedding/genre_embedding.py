"""
genre_embedding.py — 장르 선호도 벡터 생성 (128차원)

입력: extract_numeric_features() 결과 dict
출력: np.ndarray shape=(128,) dtype=float32, L2 정규화

구성 (설계서 §2.5):
  [0:67]    장르별 친화도 점수 (67개 장르, 정규화)
  [67:81]   ct_cl 분포 (14개 콘텐츠 유형, 비율)
  [81:128]  제로 패딩 (미래 확장용)
"""
import numpy as np
from config import GENRE_LIST, CT_CL_LIST, GENRE_DIM


def build_genre_vector(numeric: dict) -> np.ndarray:
    """
    수치 특징 딕셔너리 → 장르 선호도 벡터 (128차원, L2 정규화)

    Args:
        numeric: extract_numeric_features() 반환값
                 또는 {"genre_stats": {...}, "ct_cl_distribution": {...}}
    Returns:
        np.ndarray shape=(GENRE_DIM,) dtype=float32
    """
    genre_stats      = numeric.get("genre_stats", {})
    ct_cl_dist       = numeric.get("ct_cl_distribution", {})

    n_genres = len(GENRE_LIST)   # 67
    n_ct_cl  = len(CT_CL_LIST)   # 14

    # ── 슬롯 1: 장르별 친화도 ────────────────────────────────────────
    aff_vec = np.zeros(n_genres, dtype=np.float32)
    for i, genre in enumerate(GENRE_LIST):
        if genre in genre_stats:
            aff_vec[i] = float(genre_stats[genre].get("affinity", 0))
    max_aff = aff_vec.max()
    if max_aff > 0:
        aff_vec = aff_vec / max_aff

    # ── 슬롯 2: ct_cl 분포 (비율) ────────────────────────────────────
    ct_vec = np.zeros(n_ct_cl, dtype=np.float32)
    for i, ct in enumerate(CT_CL_LIST):
        ct_vec[i] = float(ct_cl_dist.get(ct, 0))
    ct_sum = ct_vec.sum()
    if ct_sum > 0:
        ct_vec = ct_vec / ct_sum

    # ── 연결 → 128차원 ──────────────────────────────────────────────
    raw = np.concatenate([aff_vec, ct_vec])   # 67 + 14 = 81
    vec = np.zeros(GENRE_DIM, dtype=np.float32)
    vec[:len(raw)] = raw

    # ── L2 정규화 ───────────────────────────────────────────────────
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.astype(np.float32)
