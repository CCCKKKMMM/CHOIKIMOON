"""
RAG 파이프라인 - VOD 메타데이터 결측치 보강

실행 순서:
  1순위: smry (줄거리)         13건
  2순위: director 영화          44건
  3순위: director TV드라마/애니 4,527건
  4순위: series_nm             431건

실행 방법:
  python rag_pipeline.py             # 전체 실행
  python rag_pipeline.py --step smry # 특정 단계만 실행
  python rag_pipeline.py --step director
  python rag_pipeline.py --step series_nm
"""

import argparse
import sys
import db
import llm
from config import DIRECTOR_TARGET_CT_CL


def run_smry(conn):
    rows = db.fetch_missing_smry(conn)
    total = len(rows)
    print(f"\n[1순위] smry 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        print(f"  [{i}/{total}] {asset_nm} ...", end=" ", flush=True)

        smry = llm.fetch_smry(
            asset_nm=asset_nm,
            ct_cl=row["ct_cl"],
            genre=row["genre"],
            director=row["director"],
        )

        if smry:
            db.update_vod(conn, asset_id, {"smry": smry})
            print(f"완료 ({len(smry)}자)")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  smry 완료: 채움 {filled}건 / 스킵 {skipped}건")


def run_director(conn):
    rows = db.fetch_missing_director(conn, DIRECTOR_TARGET_CT_CL)
    total = len(rows)
    print(f"\n[2~3순위] director 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        print(f"  [{i}/{total}] [{row['ct_cl']}] {asset_nm} ...", end=" ", flush=True)

        director = llm.fetch_director(
            asset_nm=asset_nm,
            ct_cl=row["ct_cl"],
            genre=row["genre"],
            series_nm=row["series_nm"],
        )

        if director:
            db.update_vod(conn, asset_id, {"director": director})
            print(f"완료 → {director}")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_director_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  director 완료: 채움 {filled}건 / 스킵 {skipped}건")


def run_series_nm(conn):
    rows = db.fetch_missing_series_nm(conn)
    total = len(rows)
    print(f"\n[4순위] series_nm 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        print(f"  [{i}/{total}] {asset_nm} ...", end=" ", flush=True)

        series_nm = llm.fetch_series_nm(
            asset_nm=asset_nm,
            ct_cl=row["ct_cl"],
            genre=row["genre"],
        )

        if series_nm:
            db.update_vod(conn, asset_id, {"series_nm": series_nm})
            print(f"완료 → {series_nm}")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_series_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  series_nm 완료: 채움 {filled}건 / 스킵 {skipped}건")


def print_summary(conn):
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE rag_processed = TRUE) AS processed,
                COUNT(*) FILTER (WHERE rag_source NOT LIKE 'skipped%%' AND rag_processed = TRUE) AS filled,
                COUNT(*) FILTER (WHERE rag_source LIKE 'skipped%%') AS skipped,
                COUNT(*) FILTER (WHERE rag_processed IS NOT TRUE) AS remaining
            FROM vods
        """)
        r = cur.fetchone()
    print(f"""
=== RAG 파이프라인 최종 현황 ===
  처리 완료: {r['processed']:,}건
  채움 성공: {r['filled']:,}건
  스킵:      {r['skipped']:,}건
  미처리:    {r['remaining']:,}건
""")


def main():
    parser = argparse.ArgumentParser(description="VOD RAG 파이프라인")
    parser.add_argument("--step", choices=["smry", "director", "series_nm"],
                        help="특정 단계만 실행 (생략 시 전체 실행)")
    args = parser.parse_args()

    conn = db.get_conn()
    try:
        if args.step == "smry":
            run_smry(conn)
        elif args.step == "director":
            run_director(conn)
        elif args.step == "series_nm":
            run_series_nm(conn)
        else:
            run_smry(conn)
            run_director(conn)
            run_series_nm(conn)

        print_summary(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
