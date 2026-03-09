import os

# DB 연결
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "choikimoon",
    "user": "postgres",
    "password": "0000",
}

# TMDB API
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_LANGUAGE = "ko-KR"

# Ollama (로컬 LLM - 폴백용)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"          # 설치된 모델명으로 변경 (예: "mistral", "gemma2")

# RAG 파이프라인 설정
REQUEST_DELAY = 0.3                # API 호출 간 대기 시간 (초)
MAX_RETRIES = 3                    # 실패 시 재시도 횟수

# 처리 대상 콘텐츠 타입
DIRECTOR_TARGET_CT_CL = ["영화", "TV드라마", "TV애니메이션"]
