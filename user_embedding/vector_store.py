"""
ChromaDB 벡터 저장소 모듈
"""

import chromadb
from config import CHROMA_PATH, CHROMA_COLLECTION, TOP_K


class UserVectorStore:
    """사용자 임베딩 벡터 저장 및 검색"""

    def __init__(self, path: str = CHROMA_PATH, collection: str = CHROMA_COLLECTION):
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=collection,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, user_id: str, embedding: list, metadata: dict):
        """사용자 임베딩 저장 (없으면 추가, 있으면 갱신)"""
        self.collection.upsert(
            ids=[user_id],
            embeddings=[embedding],
            metadatas=[metadata if metadata else None],
        )

    def get(self, user_id: str) -> dict | None:
        """단일 사용자 임베딩 조회"""
        result = self.collection.get(ids=[user_id], include=["embeddings", "metadatas"])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "embedding": result["embeddings"][0],
            "metadata": result["metadatas"][0],
        }

    def find_similar(self, embedding: list, top_k: int = TOP_K) -> list:
        """
        유사 사용자 검색
        Returns: [{"id": sha2_hash, "distance": float, "metadata": dict}]
        """
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, self.count()),
            include=["metadatas", "distances"],
        )
        if not results["ids"][0]:
            return []
        return [
            {
                "id": uid,
                "distance": dist,
                "metadata": meta,
            }
            for uid, dist, meta in zip(
                results["ids"][0],
                results["distances"][0],
                results["metadatas"][0],
            )
        ]

    def count(self) -> int:
        return self.collection.count()
