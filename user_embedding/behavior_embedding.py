"""
behavior_embedding.py — 행동 벡터 생성 (256차원)

입력: extract_numeric_features() 결과 dict
출력: np.ndarray shape=(256,) dtype=float32, L2 정규화

구성 (설계서 §2.5):
  [0:67]    장르별 완주율 (67개 장르)
  [67:134]  장르별 친화도 스코어 (67개 장르)
  [134:141] 요일별 시청 분포 (7개)
  [141:142] 총 시청 수 (정규화)
  [142:256] 제로 패딩 (미래 확장용)
"""
import numpy as np
from config import GENRE_LIST, BEHAVIOR_DIM, WATCH_CNT_MAX


def build_behavior_vector(numeric: dict) -> np.ndarray:
    """
    수치 특징 딕셔너리 → 행동 벡터 (256차원, L2 정규화)

    Args:
        numeric: extract_numeric_features() 반환값
    Returns:
        np.ndarray shape=(BEHAVIOR_DIM,) dtype=float32
    """
    genre_stats       = numeric.get("genre_stats", {})
    dow_distribution  = numeric.get("dow_distribution", {})
    total_watch_count = numeric.get("total_watch_count", 0)

    n_genres = len(GENRE_LIST)  # 67

    # ── 슬롯 1: 장르별 평균 완주율 (0~1) ──────────────────────────────
    cr_vec = np.zeros(n_genres, dtype=np.float32)
    for i, genre in enumerate(GENRE_LIST):
        if genre in genre_stats:
            cr_vec[i] = float(genre_stats[genre]["avg_completion_rate"])

    # ── 슬롯 2: 장르별 친화도 (count × avg_cr × avg_sat, 정규화) ──────
    aff_vec = np.zeros(n_genres, dtype=np.float32)
    for i, genre in enumerate(GENRE_LIST):
        if genre in genre_stats:
            aff_vec[i] = float(genre_stats[genre]["affinity"])
    # 최대값으로 정규화
    max_aff = aff_vec.max()
    if max_aff > 0:
        aff_vec = aff_vec / max_aff

    # ── 슬롯 3: 요일별 시청 분포 (7개, 합계로 정규화) ─────────────────
    dow_vec = np.zeros(7, dtype=np.float32)
    for dow, cnt in dow_distribution.items():
        dow_vec[int(dow)] = float(cnt)
    dow_sum = dow_vec.sum()
    if dow_sum > 0:
        dow_vec = dow_vec / dow_sum

    # ── 슬롯 4: 총 시청 수 (MinMax, 스칼라 1개) ───────────────────────
    total_norm = min(float(total_watch_count) / WATCH_CNT_MAX, 1.0)
    total_vec = np.array([total_norm], dtype=np.float32)

    # ── 연결 → 256차원 ─────────────────────────────────────────────────
    raw = np.concatenate([cr_vec, aff_vec, dow_vec, total_vec])  # 67+67+7+1 = 142
    # 나머지를 0으로 패딩하여 BEHAVIOR_DIM(256)차원 맞춤
    vec = np.zeros(BEHAVIOR_DIM, dtype=np.float32)
    vec[:len(raw)] = raw

    # ── L2 정규화 ──────────────────────────────────────────────────────
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.astype(np.float32)
