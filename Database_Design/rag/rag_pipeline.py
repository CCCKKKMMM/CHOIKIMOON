"""
RAG 파이프라인 - VOD 메타데이터 결측치 보강

소스 우선순위:
  1순위: TMDB API  (정확한 실제 데이터)
  2순위: Ollama    (로컬 LLM 폴백)

처리 단계:
  1순위: smry (줄거리)          13건
  2순위: director 영화           44건
  3순위: director TV드라마/애니  4,527건
  4순위: series_nm              431건

실행 방법:
  python rag_pipeline.py                 # 전체 실행
  python rag_pipeline.py --step smry     # 특정 단계만 실행
  python rag_pipeline.py --step director
  python rag_pipeline.py --step series_nm
  python rag_pipeline.py --tmdb-only     # TMDB만 사용 (Ollama 폴백 없음)
"""

import sys
import argparse
import db

# Windows 콘솔 인코딩 UTF-8 강제 설정
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import llm
import tmdb
from config import DIRECTOR_TARGET_CT_CL


def _is_movie(ct_cl: str) -> bool:
    return ct_cl == "영화"


def _tmdb_search(asset_nm: str, ct_cl: str) -> dict:
    if _is_movie(ct_cl):
        return tmdb.search_movie(asset_nm)
    return tmdb.search_tv(asset_nm)


def run_smry(conn, tmdb_only: bool = False):
    rows = db.fetch_missing_smry(conn)
    total = len(rows)
    print(f"\n[1순위] smry 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    tmdb_hit = ollama_hit = 0

    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        ct_cl = row["ct_cl"]
        print(f"  [{i}/{total}] {asset_nm} ...", end=" ", flush=True)

        smry = ""
        source = ""

        # 1차: TMDB
        info = _tmdb_search(asset_nm, ct_cl)
        smry = info.get("smry", "")
        if smry:
            source = "tmdb"
            tmdb_hit += 1

        # 2차: Ollama 폴백
        if not smry and not tmdb_only:
            smry = llm.fetch_smry(
                asset_nm=asset_nm,
                ct_cl=ct_cl,
                genre=row["genre"],
                director=row["director"],
            )
            if smry:
                source = "ollama"
                ollama_hit += 1

        if smry:
            db.update_vod(conn, asset_id, {"smry": smry}, source=source)
            print(f"완료 ({len(smry)}자) [{source}]")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  smry 완료: 채움 {filled}건 (TMDB {tmdb_hit} / Ollama {ollama_hit}) / 스킵 {skipped}건")


def run_director(conn, tmdb_only: bool = False):
    rows = db.fetch_missing_director(conn, DIRECTOR_TARGET_CT_CL)
    total = len(rows)
    print(f"\n[2~3순위] director 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    tmdb_hit = ollama_hit = 0

    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        ct_cl = row["ct_cl"]
        print(f"  [{i}/{total}] [{ct_cl}] {asset_nm} ...", end=" ", flush=True)

        director = ""
        source = ""

        # 1차: TMDB
        info = _tmdb_search(asset_nm, ct_cl)
        director = info.get("director", "")
        if director:
            source = "tmdb"
            tmdb_hit += 1

        # 2차: Ollama 폴백
        if not director and not tmdb_only:
            director = llm.fetch_director(
                asset_nm=asset_nm,
                ct_cl=ct_cl,
                genre=row["genre"],
                series_nm=row["series_nm"],
            )
            if director:
                source = "ollama"
                ollama_hit += 1

        if director:
            db.update_vod(conn, asset_id, {"director": director}, source=source)
            print(f"완료 → {director} [{source}]")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_director_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  director 완료: 채움 {filled}건 (TMDB {tmdb_hit} / Ollama {ollama_hit}) / 스킵 {skipped}건")


def run_series_nm(conn, tmdb_only: bool = False):
    rows = db.fetch_missing_series_nm(conn)
    total = len(rows)
    print(f"\n[4순위] series_nm 보강 시작: {total}건")
    if total == 0:
        print("  처리 대상 없음")
        return

    filled = skipped = 0
    tmdb_hit = ollama_hit = 0

    for i, row in enumerate(rows, 1):
        asset_id = row["full_asset_id"]
        asset_nm = row["asset_nm"]
        ct_cl = row["ct_cl"]
        print(f"  [{i}/{total}] {asset_nm} ...", end=" ", flush=True)

        series_nm = ""
        source = ""

        # 1차: TMDB (TV 검색)
        info = tmdb.search_tv(asset_nm)
        series_nm = info.get("series_nm", "")
        if series_nm:
            source = "tmdb"
            tmdb_hit += 1

        # 2차: Ollama 폴백
        if not series_nm and not tmdb_only:
            series_nm = llm.fetch_series_nm(
                asset_nm=asset_nm,
                ct_cl=ct_cl,
                genre=row["genre"],
            )
            if series_nm:
                source = "ollama"
                ollama_hit += 1

        if series_nm:
            db.update_vod(conn, asset_id, {"series_nm": series_nm}, source=source)
            print(f"완료 → {series_nm} [{source}]")
            filled += 1
        else:
            db.mark_rag_skipped(conn, asset_id, reason="no_series_info")
            print("정보 없음 (스킵)")
            skipped += 1

    print(f"\n  series_nm 완료: 채움 {filled}건 (TMDB {tmdb_hit} / Ollama {ollama_hit}) / 스킵 {skipped}건")


def print_summary(conn):
    import psycopg2.extras
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE rag_processed = TRUE)                        AS processed,
                COUNT(*) FILTER (WHERE rag_source = 'tmdb')                         AS tmdb_filled,
                COUNT(*) FILTER (WHERE rag_source = 'ollama')                       AS ollama_filled,
                COUNT(*) FILTER (WHERE rag_source LIKE 'skipped%%')                 AS skipped,
                COUNT(*) FILTER (WHERE rag_processed IS NOT TRUE)                   AS remaining
            FROM vods
        """)
        r = cur.fetchone()
    print(f"""
=== RAG 파이프라인 최종 현황 ===
  처리 완료:     {r['processed']:,}건
  TMDB 채움:    {r['tmdb_filled']:,}건
  Ollama 채움:  {r['ollama_filled']:,}건
  스킵:          {r['skipped']:,}건
  미처리:        {r['remaining']:,}건
""")


def main():
    parser = argparse.ArgumentParser(description="VOD RAG 파이프라인 (TMDB + Ollama)")
    parser.add_argument("--step", choices=["smry", "director", "series_nm"],
                        help="특정 단계만 실행 (생략 시 전체 실행)")
    parser.add_argument("--tmdb-only", action="store_true",
                        help="TMDB만 사용 (Ollama 폴백 비활성화)")
    args = parser.parse_args()

    conn = db.get_conn()
    try:
        kwargs = {"tmdb_only": args.tmdb_only}
        if args.step == "smry":
            run_smry(conn, **kwargs)
        elif args.step == "director":
            run_director(conn, **kwargs)
        elif args.step == "series_nm":
            run_series_nm(conn, **kwargs)
        else:
            run_smry(conn, **kwargs)
            run_director(conn, **kwargs)
            run_series_nm(conn, **kwargs)

        print_summary(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
