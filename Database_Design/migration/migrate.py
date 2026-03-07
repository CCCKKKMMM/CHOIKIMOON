import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

# DB 연결 설정
CONN_INFO = {
    "host": "localhost",
    "port": 5432,
    "dbname": "choikimoon",
    "user": "postgres",
    "password": "0000"
}

CSV_PATHS = {
    "users":         "C:/Users/user/Downloads/user_table.csv",
    "vods":          "C:/Users/user/Downloads/vod_table.csv",
    "watch_history": "C:/Users/user/Downloads/watch_history_table.csv",
}

def to_none(val):
    """NaN, '알수없음', 빈 문자열 → None"""
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if str(val).strip() in ('', '알수없음', 'nan', 'NaN', 'NULL', 'null'):
        return None
    return val


def migrate_users(conn):
    print("[1/3] users 테이블 import 시작...")
    df = pd.read_csv(CSV_PATHS["users"], dtype=str)
    df.columns = [c.lower() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        rows.append((
            to_none(row.get("sha2_hash")),
            to_none(row.get("age_grp10")),
            to_none(row.get("inhome_rate")),
            to_none(row.get("svod_scrb_cnt_grp")),
            to_none(row.get("paid_chnl_cnt_grp")),
            to_none(row.get("ch_hh_avg_month1")),
            to_none(row.get("kids_use_pv_month1")),
            to_none(row.get("nfx_use_yn")),
        ))

    sql = """
        INSERT INTO users (sha2_hash, age_grp10, inhome_rate, svod_scrb_cnt_grp,
                           paid_chnl_cnt_grp, ch_hh_avg_month1, kids_use_pv_month1, nfx_use_yn)
        VALUES %s ON CONFLICT (sha2_hash) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=5000)
    conn.commit()
    print(f"  → {len(rows):,}건 완료")


def migrate_vods(conn):
    print("[2/3] vods 테이블 import 시작...")
    df = pd.read_csv(CSV_PATHS["vods"], dtype=str)
    df.columns = [c.lower() for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        rows.append((
            to_none(row.get("full_asset_id")),
            to_none(row.get("asset_nm")),
            to_none(row.get("ct_cl")),
            to_none(row.get("disp_rtm")),
            to_none(row.get("disp_rtm_sec")),
            to_none(row.get("genre")),
            to_none(row.get("director")),
            to_none(row.get("asset_prod")),
            to_none(row.get("smry")),
            to_none(row.get("provider")),
            to_none(row.get("genre_detail")),
            to_none(row.get("series_nm")),
        ))

    sql = """
        INSERT INTO vods (full_asset_id, asset_nm, ct_cl, disp_rtm, disp_rtm_sec,
                          genre, director, asset_prod, smry, provider, genre_detail, series_nm)
        VALUES %s ON CONFLICT (full_asset_id) DO NOTHING
    """
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=5000)
    conn.commit()
    print(f"  → {len(rows):,}건 완료")


def migrate_watch_history(conn):
    print("[3/3] watch_history 테이블 import 시작 (약 400만 건, 시간 소요)...")
    chunksize = 50000
    total = 0

    for chunk in pd.read_csv(CSV_PATHS["watch_history"], dtype=str, chunksize=chunksize):
        chunk.columns = [c.lower() for c in chunk.columns]
        rows = []
        for _, row in chunk.iterrows():
            rows.append((
                to_none(row.get("sha2_hash")),
                to_none(row.get("full_asset_id")),
                to_none(row.get("strt_dt")),
                to_none(row.get("use_tms")),
                to_none(row.get("completion_rate")),
                to_none(row.get("satisfaction")),
            ))

        sql = """
            INSERT INTO watch_history (sha2_hash, full_asset_id, strt_dt, use_tms, completion_rate, satisfaction)
            VALUES %s
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows, page_size=5000)
        conn.commit()
        total += len(rows)
        print(f"  → {total:,}건 처리 중...")

    print(f"  → 총 {total:,}건 완료")


def main():
    print("PostgreSQL 연결 중...")
    conn = psycopg2.connect(**CONN_INFO)
    print("연결 성공\n")

    try:
        migrate_users(conn)
        migrate_vods(conn)
        migrate_watch_history(conn)

        # 최종 확인
        print("\n=== 최종 확인 ===")
        with conn.cursor() as cur:
            for table in ["users", "vods", "watch_history"]:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table}: {count:,}건")
    finally:
        conn.close()

    print("\nMigration 완료!")


if __name__ == "__main__":
    main()
