import os

# DB 연결
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "choikimoon",
    "user": "postgres",
    "password": "0000",
}

# Claude API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-6"

# RAG 파이프라인 설정
BATCH_SIZE = 10          # 1회 API 호출당 처리 건수
REQUEST_DELAY = 0.5      # API 호출 간 대기 시간 (초)
MAX_RETRIES = 3          # 실패 시 재시도 횟수

# 처리 대상 콘텐츠 타입 (RAG 효과 높은 순)
DIRECTOR_TARGET_CT_CL = ["영화", "TV드라마", "TV애니메이션"]
