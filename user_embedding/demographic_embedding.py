"""
demographic_embedding.py — 인구통계 벡터 생성 (64차원)

입력: extract_numeric_features() 결과 dict
출력: np.ndarray shape=(64,) dtype=float32, L2 정규화

구성 (설계서 §2.5):
  [0:10]   age_grp10 원핫 인코딩 (10개 그룹)
  [10]     inhome_rate (0~1)
  [11]     nfx_use_yn (0/1)
  [12]     svod_scrb_cnt_grp 정규화 (0~1)
  [13]     paid_chnl_cnt_grp 정규화 (0~1)
  [14]     ch_hh_avg_month1 정규화 (0~1)
  [15]     kids_use_pv_month1 정규화 (0~1)
  [16:64]  제로 패딩 (미래 확장용)
"""
import numpy as np
from config import (
    AGE_GRP_LIST, DEMOGRAPHIC_DIM,
    CH_HH_MAX, KIDS_PV_MAX, SVOD_MAX, PAID_CHNL_MAX,
)


def build_demographic_vector(numeric: dict) -> np.ndarray:
    """
    인구통계 특징 딕셔너리 → 64차원 벡터 (L2 정규화)

    Args:
        numeric: extract_numeric_features() 반환값 또는 동일 키 dict
    Returns:
        np.ndarray shape=(DEMOGRAPHIC_DIM,) dtype=float32
    """
    age_grp10         = numeric.get("age_grp10")
    inhome_rate       = float(numeric.get("inhome_rate") or 0)
    nfx_use_yn        = numeric.get("nfx_use_yn")
    svod_scrb_cnt_grp = numeric.get("svod_scrb_cnt_grp")
    paid_chnl_cnt_grp = numeric.get("paid_chnl_cnt_grp")
    ch_hh_avg_month1  = float(numeric.get("ch_hh_avg_month1") or 0)
    kids_use_pv_month1 = float(numeric.get("kids_use_pv_month1") or 0)

    vec = np.zeros(DEMOGRAPHIC_DIM, dtype=np.float32)

    # ── 연령대 원핫 (0~9번 인덱스) ─────────────────────────────────
    if age_grp10 and age_grp10 in AGE_GRP_LIST:
        idx = AGE_GRP_LIST.index(age_grp10)
    else:
        idx = AGE_GRP_LIST.index("unknown")  # 마지막 인덱스
    vec[idx] = 1.0

    # ── 수치 스칼라 (10~15번 인덱스) ──────────────────────────────
    vec[10] = min(inhome_rate, 1.0)
    vec[11] = 1.0 if nfx_use_yn == "Y" else 0.0

    # svod_scrb_cnt_grp, paid_chnl_cnt_grp는 문자열로 저장됨
    try:
        svod_val = float(svod_scrb_cnt_grp or 0)
    except (ValueError, TypeError):
        svod_val = 0.0
    vec[12] = min(svod_val / SVOD_MAX, 1.0)

    try:
        paid_val = float(paid_chnl_cnt_grp or 0)
    except (ValueError, TypeError):
        paid_val = 0.0
    vec[13] = min(paid_val / PAID_CHNL_MAX, 1.0)

    vec[14] = min(ch_hh_avg_month1 / CH_HH_MAX, 1.0)
    vec[15] = min(kids_use_pv_month1 / KIDS_PV_MAX, 1.0)

    # ── L2 정규화 ──────────────────────────────────────────────────
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.astype(np.float32)
