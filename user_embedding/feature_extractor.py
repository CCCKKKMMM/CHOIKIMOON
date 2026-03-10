"""
사용자 특징 추출 모듈

watch_history + users 테이블에서 사용자 특징을 추출하여
임베딩용 텍스트로 변환한다.
"""

from psycopg2.extras import RealDictCursor
from config import WATCH_HISTORY_DAYS


def extract_user_features(conn, sha2_hash: str) -> dict:
    """
    DB에서 사용자의 시청 이력 기반 특징 추출
    Returns:
        {
            avg_satisfaction, avg_completion_rate, total_watch_count,
            top_genres (list), top_ct_cls (list)
        }
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 시청 통계
        cur.execute("""
            SELECT
                ROUND(AVG(satisfaction)::numeric, 2)    AS avg_satisfaction,
                ROUND(AVG(completion_rate)::numeric, 2) AS avg_completion_rate,
                COUNT(*)                                AS total_watch_count
            FROM watch_history
            WHERE sha2_hash = %s
        """, (sha2_hash,))
        stats = cur.fetchone() or {}

        # 선호 장르 (상위 3개)
        cur.execute("""
            SELECT v.genre, COUNT(*) AS cnt
            FROM watch_history wh
            JOIN vods v ON wh.full_asset_id = v.full_asset_id
            WHERE wh.sha2_hash = %s AND v.genre IS NOT NULL
            GROUP BY v.genre
            ORDER BY cnt DESC
            LIMIT 3
        """, (sha2_hash,))
        top_genres = [r["genre"] for r in cur.fetchall()]

        # 선호 콘텐츠 타입 (상위 2개)
        cur.execute("""
            SELECT v.ct_cl, COUNT(*) AS cnt
            FROM watch_history wh
            JOIN vods v ON wh.full_asset_id = v.full_asset_id
            WHERE wh.sha2_hash = %s AND v.ct_cl IS NOT NULL
            GROUP BY v.ct_cl
            ORDER BY cnt DESC
            LIMIT 2
        """, (sha2_hash,))
        top_ct_cls = [r["ct_cl"] for r in cur.fetchall()]

    return {
        "avg_satisfaction":   float(stats.get("avg_satisfaction") or 0),
        "avg_completion_rate": float(stats.get("avg_completion_rate") or 0),
        "total_watch_count":  int(stats.get("total_watch_count") or 0),
        "top_genres":         top_genres,
        "top_ct_cls":         top_ct_cls,
    }


def extract_numeric_features(conn, sha2_hash: str, days: int = WATCH_HISTORY_DAYS) -> dict:
    """
    멀티벡터 임베딩용 수치 특징 추출 (최근 N일 시청 이력 기반)

    Returns:
        {
            genre_stats: { genre → {count, avg_completion_rate, avg_satisfaction, affinity} },
            dow_distribution: { int(0-6) → count },
            total_watch_count: int,
            age_grp10, inhome_rate, svod_scrb_cnt_grp, paid_chnl_cnt_grp,
            ch_hh_avg_month1, kids_use_pv_month1, nfx_use_yn
        }
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # ① 장르별 통계 (완주율·만족도·친화도)
        cur.execute("""
            SELECT
                v.genre,
                COUNT(*)                                    AS cnt,
                ROUND(AVG(wh.completion_rate)::numeric, 4) AS avg_cr,
                ROUND(AVG(wh.satisfaction)::numeric, 4)    AS avg_sat
            FROM watch_history wh
            JOIN vods v ON wh.full_asset_id = v.full_asset_id
            WHERE wh.sha2_hash = %s
              AND v.genre IS NOT NULL
              AND wh.strt_dt >= NOW() - INTERVAL '%s days'
            GROUP BY v.genre
            ORDER BY cnt DESC
        """, (sha2_hash, days))
        genre_rows = cur.fetchall()

        # ② 요일별 시청 분포 (0=일요일, 6=토요일)
        cur.execute("""
            SELECT
                EXTRACT(DOW FROM strt_dt)::int AS dow,
                COUNT(*)                       AS cnt
            FROM watch_history
            WHERE sha2_hash = %s
              AND strt_dt >= NOW() - INTERVAL '%s days'
            GROUP BY dow
            ORDER BY dow
        """, (sha2_hash, days))
        dow_rows = cur.fetchall()

        # ③ 총 시청 수
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM watch_history
            WHERE sha2_hash = %s
              AND strt_dt >= NOW() - INTERVAL '%s days'
        """, (sha2_hash, days))
        total_row = cur.fetchone() or {"total": 0}

        # ④ 인구통계
        cur.execute("""
            SELECT age_grp10, inhome_rate, svod_scrb_cnt_grp, paid_chnl_cnt_grp,
                   ch_hh_avg_month1, kids_use_pv_month1, nfx_use_yn
            FROM users
            WHERE sha2_hash = %s
        """, (sha2_hash,))
        user_row = cur.fetchone()

    # -- genre_stats 조립
    genre_stats = {}
    for r in genre_rows:
        cnt    = int(r["cnt"])
        avg_cr = float(r["avg_cr"] or 0)
        avg_sat = float(r["avg_sat"] or 0)
        genre_stats[r["genre"]] = {
            "count":               cnt,
            "avg_completion_rate": avg_cr,
            "avg_satisfaction":    avg_sat,
            "affinity":            cnt * avg_cr * avg_sat,
        }

    # -- dow_distribution 조립
    dow_distribution = {int(r["dow"]): int(r["cnt"]) for r in dow_rows}

    # -- demographics
    u = user_row or {}
    return {
        "genre_stats":         genre_stats,
        "dow_distribution":    dow_distribution,
        "total_watch_count":   int(total_row.get("total") or 0),
        "age_grp10":           u.get("age_grp10"),
        "inhome_rate":         float(u.get("inhome_rate") or 0),
        "svod_scrb_cnt_grp":   u.get("svod_scrb_cnt_grp"),
        "paid_chnl_cnt_grp":   u.get("paid_chnl_cnt_grp"),
        "ch_hh_avg_month1":    float(u.get("ch_hh_avg_month1") or 0),
        "kids_use_pv_month1":  float(u.get("kids_use_pv_month1") or 0),
        "nfx_use_yn":          u.get("nfx_use_yn"),
    }


def build_user_feature_text(user: dict, history: dict) -> str:
    """
    사용자 특징 딕셔너리 → 임베딩용 자연어 텍스트 변환
    """
    parts = []

    age = user.get("age_grp10")
    if age:
        parts.append(f"연령대: {age}")

    genres = history.get("top_genres", [])
    if genres:
        parts.append(f"선호 장르: {', '.join(genres)}")

    ct_cls = history.get("top_ct_cls", [])
    if ct_cls:
        parts.append(f"선호 콘텐츠: {', '.join(ct_cls)}")

    avg_sat = history.get("avg_satisfaction", 0)
    if avg_sat:
        parts.append(f"평균 만족도: {avg_sat:.1f}")

    avg_comp = history.get("avg_completion_rate", 0)
    if avg_comp:
        parts.append(f"평균 완료율: {avg_comp:.0%}")

    watch_cnt = history.get("total_watch_count", 0)
    if watch_cnt:
        parts.append(f"총 시청 수: {watch_cnt}편")

    inhome = user.get("inhome_rate")
    if inhome is not None:
        label = "집에서 주로 시청" if inhome >= 0.5 else "외부에서 주로 시청"
        parts.append(label)

    if user.get("nfx_use_yn") == "Y":
        parts.append("넷플릭스 이용자")

    if user.get("kids_use_pv_month1", 0):
        parts.append("키즈 콘텐츠 이용")

    return ". ".join(parts) if parts else "신규 사용자"
