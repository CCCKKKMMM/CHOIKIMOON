import os

# DB 연결
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "choikimoon"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "0000"),
}

# 임베딩 모델
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # sentence-transformers 경량 모델
EMBEDDING_DIM = 384                      # all-MiniLM-L6-v2 차원 수

# ChromaDB
CHROMA_PATH = "./chroma_db"             # 벡터 저장 경로
CHROMA_COLLECTION = "user_embeddings"

# 파이프라인
BATCH_SIZE = 1000                        # 한 번에 처리할 사용자 수
TOP_K = 10                               # 유사 사용자 검색 개수
