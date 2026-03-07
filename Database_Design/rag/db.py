import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from config import DB_CONFIG


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ── 1순위: smry 결측 행 조회 ──────────────────────────────────────────
def fetch_missing_smry(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT full_asset_id, asset_nm, ct_cl, genre, director, genre_detail
            FROM vods
            WHERE (smry IS NULL OR smry = '')
              AND (rag_processed IS NULL OR rag_processed = FALSE)
            ORDER BY ct_cl, asset_nm
        """)
        return cur.fetchall()


# ── 2~3순위: director 결측 행 조회 ───────────────────────────────────
def fetch_missing_director(conn, ct_cl_list):
    placeholders = ",".join(["%s"] * len(ct_cl_list))
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(f"""
            SELECT full_asset_id, asset_nm, ct_cl, genre, genre_detail,
                   series_nm, smry
            FROM vods
            WHERE (director IS NULL OR director = '' OR director = '-')
              AND ct_cl IN ({placeholders})
              AND (rag_processed IS NULL OR rag_processed = FALSE)
            ORDER BY ct_cl, asset_nm
        """, ct_cl_list)
        return cur.fetchall()


# ── 4순위: series_nm 결측 행 조회 ────────────────────────────────────
def fetch_missing_series_nm(conn):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT full_asset_id, asset_nm, ct_cl, genre, director
            FROM vods
            WHERE (series_nm IS NULL OR series_nm = '')
              AND ct_cl IN ('TV드라마', 'TV애니메이션')
              AND (rag_processed IS NULL OR rag_processed = FALSE)
            ORDER BY asset_nm
        """)
        return cur.fetchall()


# ── DB 업데이트 ───────────────────────────────────────────────────────
def update_vod(conn, full_asset_id: str, updates: dict, source: str = "claude-sonnet-4-6"):
    """updates: {'smry': '...', 'director': '...'} 형태"""
    if not updates:
        return

    set_clauses = [f"{col} = %s" for col in updates]
    set_clauses += ["rag_processed = TRUE", "rag_source = %s", "rag_processed_at = %s"]
    values = list(updates.values()) + [source, datetime.now(), full_asset_id]

    sql = f"""
        UPDATE vods
        SET {', '.join(set_clauses)}
        WHERE full_asset_id = %s
    """
    with conn.cursor() as cur:
        cur.execute(sql, values)
    conn.commit()


def mark_rag_skipped(conn, full_asset_id: str, reason: str = "no_info"):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE vods
            SET rag_processed = TRUE, rag_source = %s, rag_processed_at = %s
            WHERE full_asset_id = %s
        """, (f"skipped:{reason}", datetime.now(), full_asset_id))
    conn.commit()
