"""
User Embedding 파이프라인

실행 방법:
  python pipeline.py                    # 전체 사용자 임베딩 생성
  python pipeline.py --limit 1000       # 최대 1000명만 처리
  python pipeline.py --user <sha2_hash> # 특정 사용자만
  python pipeline.py --find <sha2_hash> # 유사 사용자 검색
"""

import sys
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor

from config import DB_CONFIG, BATCH_SIZE, TOP_K
from feature_extractor import extract_user_features, build_user_feature_text
from embedding import EmbeddingModel, generate_embedding
from vector_store import UserVectorStore

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def run_all(limit: int = None):
    """전체 사용자 임베딩 생성"""
    conn = get_conn()
    model = EmbeddingModel()
    store = UserVectorStore()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = "SELECT * FROM users ORDER BY sha2_hash"
        if limit:
            query += f" LIMIT {limit}"
        cur.execute(query)
        users = cur.fetchall()

    total = len(users)
    print(f"\n[User Embedding] 총 {total:,}명 처리 시작")

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
    print(f"\n완료: 총 {success:,}명 임베딩 저장, 벡터 DB 크기: {store.count():,}개")


def run_single(sha2_hash: str):
    """단일 사용자 임베딩 생성"""
    conn = get_conn()
    model = EmbeddingModel()
    store = UserVectorStore()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM users WHERE sha2_hash = %s", (sha2_hash,))
        user = cur.fetchone()

    if not user:
        print(f"사용자를 찾을 수 없습니다: {sha2_hash}")
        return

    history = extract_user_features(conn, sha2_hash)
    text = build_user_feature_text(dict(user), history)
    print(f"\n[특징 텍스트]\n{text}")

    vec = generate_embedding(text, model)
    metadata = {
        "age_grp10":  user.get("age_grp10") or "",
        "nfx_use_yn": user.get("nfx_use_yn") or "N",
        "top_genres": ",".join(history["top_genres"]),
        "watch_count": str(history["total_watch_count"]),
    }
    store.upsert(sha2_hash, vec, metadata)
    print(f"임베딩 저장 완료 (dim={len(vec)})")
    conn.close()


def find_similar(sha2_hash: str, top_k: int = TOP_K):
    """유사 사용자 검색"""
    store = UserVectorStore()
    result = store.get(sha2_hash)
    if not result:
        print(f"임베딩이 없습니다. 먼저 --user {sha2_hash} 로 생성하세요.")
        return

    similar = store.find_similar(result["embedding"], top_k=top_k)
    print(f"\n[유사 사용자 Top {top_k}]")
    for rank, s in enumerate(similar, 1):
        meta = s["metadata"] or {}
        print(f"  {rank}. {s['id'][:12]}... | 거리: {s['distance']:.4f} | "
              f"연령: {meta.get('age_grp10','?')} | 장르: {meta.get('top_genres','?')}")


def main():
    parser = argparse.ArgumentParser(description="User Embedding 파이프라인")
    parser.add_argument("--limit", type=int, help="처리할 최대 사용자 수")
    parser.add_argument("--user", type=str, help="특정 사용자 sha2_hash")
    parser.add_argument("--find", type=str, help="유사 사용자 검색할 sha2_hash")
    parser.add_argument("--top-k", type=int, default=TOP_K, help="유사 사용자 검색 수")
    args = parser.parse_args()

    if args.find:
        find_similar(args.find, top_k=args.top_k)
    elif args.user:
        run_single(args.user)
    else:
        run_all(limit=args.limit)


if __name__ == "__main__":
    main()
