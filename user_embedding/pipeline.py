"""
User Embedding 파이프라인 (멀티벡터 448차원)

실행 방법:
  python pipeline.py                    # 전체 사용자 임베딩 생성 (v2, 448차원)
  python pipeline.py --limit 1000       # 최대 1000명만 처리
  python pipeline.py --user <sha2_hash> # 특정 사용자만
  python pipeline.py --find <sha2_hash> # 유사 사용자 검색
  python pipeline.py --legacy           # 구버전 텍스트 임베딩 (384차원)
"""

import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from config import (
    DB_CONFIG, BATCH_SIZE, TOP_K,
    CHROMA_COLLECTION, CHROMA_COLLECTION_V2,
    HYBRID_DIM, BEHAVIOR_DIM, GENRE_DIM, DEMOGRAPHIC_DIM,
    WATCH_HISTORY_DAYS,
)
from feature_extractor import (
    extract_user_features, build_user_feature_text,
    extract_numeric_features,
)
from multivector_embedding import build_hybrid_vector
from embedding import EmbeddingModel, generate_embedding
from vector_store import UserVectorStore


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


# ── 멀티벡터 파이프라인 (v2) ───────────────────────────────────────────

def _save_embedding_meta(cur, sha2_hash: str, embedding_type: str,
                         dim: int, record_count: int):
    """user_embedding_meta 테이블에 메타 저장 (upsert)"""
    cur.execute("""
        INSERT INTO user_embedding_meta
            (sha2_hash, embedding_type, embedding_dimension, embedding_model,
             base_record_count, watch_history_days)
        VALUES (%s, %s, %s, 'numeric_composite_v1', %s, %s)
        ON CONFLICT (sha2_hash, embedding_type)
        DO UPDATE SET
            embedding_dimension = EXCLUDED.embedding_dimension,
            base_record_count   = EXCLUDED.base_record_count,
            updated_at          = NOW()
    """, (sha2_hash, embedding_type, dim, record_count, WATCH_HISTORY_DAYS))


def run_all(limit: int = None):
    """전체 사용자 멀티벡터 임베딩 생성 (448차원)"""
    conn = get_conn()
    store = UserVectorStore(collection=CHROMA_COLLECTION_V2)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = "SELECT sha2_hash FROM users ORDER BY sha2_hash"
        if limit:
            query += f" LIMIT {limit}"
        cur.execute(query)
        sha2_list = [r["sha2_hash"] for r in cur.fetchall()]

    total = len(sha2_list)
    print(f"\n[User Embedding v2] 총 {total:,}명 처리 시작 (448차원 멀티벡터)")

    success = skipped = 0
    for i, sha2_hash in enumerate(sha2_list, 1):
        try:
            numeric = extract_numeric_features(conn, sha2_hash)
            hybrid_vec = build_hybrid_vector(numeric)

            metadata = {
                "age_grp10":  numeric.get("age_grp10") or "",
                "nfx_use_yn": numeric.get("nfx_use_yn") or "N",
                "total_watch": str(numeric.get("total_watch_count", 0)),
            }
            store.upsert(sha2_hash, hybrid_vec.tolist(), metadata)

            # PostgreSQL 메타 저장
            with conn.cursor() as cur:
                _save_embedding_meta(
                    cur, sha2_hash, "HYBRID", HYBRID_DIM,
                    numeric.get("total_watch_count", 0),
                )
            conn.commit()

            success += 1
        except Exception as e:
            conn.rollback()
            print(f"  [SKIP] {sha2_hash[:8]}... 오류: {e}")
            skipped += 1

        if i % BATCH_SIZE == 0 or i == total:
            print(f"  진행: {i:,}/{total:,} (성공 {success:,} / 스킵 {skipped})")

    conn.close()
    print(f"\n완료: 총 {success:,}명 임베딩 저장, 벡터 DB 크기: {store.count():,}개")


def run_single(sha2_hash: str):
    """단일 사용자 멀티벡터 임베딩 생성"""
    conn = get_conn()
    store = UserVectorStore(collection=CHROMA_COLLECTION_V2)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT sha2_hash FROM users WHERE sha2_hash = %s", (sha2_hash,))
        user = cur.fetchone()

    if not user:
        print(f"사용자를 찾을 수 없습니다: {sha2_hash}")
        conn.close()
        return

    numeric = extract_numeric_features(conn, sha2_hash)
    hybrid_vec = build_hybrid_vector(numeric)

    top_genres = sorted(
        numeric.get("genre_stats", {}).items(),
        key=lambda x: x[1]["affinity"], reverse=True
    )[:3]
    print(f"\n[특징 요약]")
    print(f"  연령: {numeric.get('age_grp10')}, 재택율: {numeric.get('inhome_rate', 0):.0%}")
    print(f"  총 시청(90일): {numeric.get('total_watch_count')}편")
    print(f"  선호 장르: {[g for g, _ in top_genres]}")
    print(f"  하이브리드 벡터: {hybrid_vec.shape[0]}차원")

    metadata = {
        "age_grp10":  numeric.get("age_grp10") or "",
        "nfx_use_yn": numeric.get("nfx_use_yn") or "N",
        "total_watch": str(numeric.get("total_watch_count", 0)),
    }
    store.upsert(sha2_hash, hybrid_vec.tolist(), metadata)

    with conn.cursor() as cur:
        _save_embedding_meta(
            cur, sha2_hash, "HYBRID", HYBRID_DIM,
            numeric.get("total_watch_count", 0),
        )
    conn.commit()
    conn.close()
    print(f"임베딩 저장 완료")


def find_similar(sha2_hash: str, top_k: int = TOP_K):
    """유사 사용자 검색"""
    store = UserVectorStore(collection=CHROMA_COLLECTION_V2)
    result = store.get(sha2_hash)
    if not result:
        print(f"임베딩이 없습니다. 먼저 --user {sha2_hash} 로 생성하세요.")
        return

    similar = store.find_similar(result["embedding"], top_k=top_k)
    print(f"\n[유사 사용자 Top {top_k}]")
    for rank, s in enumerate(similar, 1):
        meta = s["metadata"] or {}
        print(f"  {rank}. {s['id'][:12]}... | 거리: {s['distance']:.4f} | "
              f"연령: {meta.get('age_grp10','?')} | 시청: {meta.get('total_watch','?')}편")


# ── 구버전 텍스트 임베딩 (레거시) ─────────────────────────────────────

def run_all_legacy(limit: int = None):
    """구버전 384차원 텍스트 임베딩 생성"""
    conn = get_conn()
    model = EmbeddingModel()
    store = UserVectorStore(collection=CHROMA_COLLECTION)

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = "SELECT * FROM users ORDER BY sha2_hash"
        if limit:
            query += f" LIMIT {limit}"
        cur.execute(query)
        users = cur.fetchall()

    total = len(users)
    print(f"\n[User Embedding v1 레거시] 총 {total:,}명 처리 (384차원 텍스트)")

    success = skipped = 0
    for i, user in enumerate(users, 1):
        sha2_hash = user["sha2_hash"]
        try:
            history = extract_user_features(conn, sha2_hash)
            text = build_user_feature_text(dict(user), history)
            vec = generate_embedding(text, model)
            metadata = {
                "age_grp10":  user.get("age_grp10") or "",
                "nfx_use_yn": user.get("nfx_use_yn") or "N",
                "top_genres": ",".join(history["top_genres"]),
                "watch_count": str(history["total_watch_count"]),
            }
            store.upsert(sha2_hash, vec, metadata)
            success += 1
        except Exception as e:
            print(f"  [SKIP] {sha2_hash[:8]}... 오류: {e}")
            skipped += 1

        if i % BATCH_SIZE == 0 or i == total:
            print(f"  진행: {i:,}/{total:,} (성공 {success:,} / 스킵 {skipped})")

    conn.close()
    print(f"\n완료: 총 {success:,}명 임베딩 저장")


def main():
    parser = argparse.ArgumentParser(description="User Embedding 파이프라인")
    parser.add_argument("--limit", type=int, help="처리할 최대 사용자 수")
    parser.add_argument("--user", type=str, help="특정 사용자 sha2_hash")
    parser.add_argument("--find", type=str, help="유사 사용자 검색할 sha2_hash")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="유사 사용자 검색 수")
    parser.add_argument("--legacy", action="store_true", help="구버전 텍스트 임베딩 사용")
    args = parser.parse_args()

    if args.find:
        find_similar(args.find, top_k=args.top_k)
    elif args.user:
        run_single(args.user)
    elif args.legacy:
        run_all_legacy(limit=args.limit)
    else:
        run_all(limit=args.limit)


if __name__ == "__main__":
    main()
