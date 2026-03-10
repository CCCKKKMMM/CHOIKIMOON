import os

# DB 연결
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 5432)),
    "dbname": os.environ.get("DB_NAME", "choikimoon"),
    "user": os.environ.get("DB_USER", "postgres"),
    "password": os.environ.get("DB_PASSWORD", "0000"),
}

# ── 텍스트 임베딩 (하위 호환 유지) ──────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# ── 멀티벡터 차원 설계 (설계서 §2.5) ──────────────────────────────────
BEHAVIOR_DIM    = 256   # 행동 벡터: 장르별 완주율 + 요일 분포 + 집계 스칼라
GENRE_DIM       = 128   # 장르 선호도 벡터: 장르별 친화도(cnt×cr×sat) + ct_cl 비율
DEMOGRAPHIC_DIM = 64    # 인구통계 벡터: 연령 원핫 + 6개 스칼라
HYBRID_DIM      = BEHAVIOR_DIM + GENRE_DIM + DEMOGRAPHIC_DIM  # 448

# 정규화 기준값 (MinMax 스케일링용)
WATCH_CNT_MAX       = 500     # 총 시청 수 정규화 기준
WEEKLY_WATCH_MAX    = 20      # 주간 평균 시청 수 정규화 기준
CH_HH_MAX           = 500.0   # 월 평균 TV 시청 시간 정규화 기준
KIDS_PV_MAX         = 100.0   # 키즈 콘텐츠 시청 수 정규화 기준
SVOD_MAX            = 10.0    # svod_scrb_cnt_grp 정규화 기준
PAID_CHNL_MAX       = 10.0    # paid_chnl_cnt_grp 정규화 기준

# ── 파이프라인 설정 ──────────────────────────────────────────────────
WATCH_HISTORY_DAYS = 90       # 시청 이력 조회 기간 (설계서 §4.2)
BATCH_SIZE         = 1000
TOP_K              = 10

# ── ChromaDB ─────────────────────────────────────────────────────────
CHROMA_PATH           = "./chroma_db"
CHROMA_COLLECTION     = "user_embeddings"      # 텍스트 384차원 (구버전)
CHROMA_COLLECTION_V2  = "user_embeddings_v2"   # 멀티벡터 448차원 (신버전)

# ── 고정 목록 (DB에서 확인한 실제 값, 순서 불변) ──────────────────────
GENRE_LIST = [
    "SF/메카", "SF/환타지", "격투기", "경제", "골프", "공포/스릴러",
    "교양", "교양다큐", "국내", "기타", "뉴스", "뉴스/시사",
    "다이어트", "다큐멘터리", "단편", "동물", "드라마", "레슬링",
    "레저", "로맨틱코미디", "리빙", "멜로", "명랑/코믹", "무협",
    "무협/환타지", "문화", "문화/예술", "뮤지컬", "미니시리즈",
    "미용/패션", "서부", "성인", "쇼", "스페셜", "스포츠",
    "시사/교양", "시트콤", "애니메이션", "액션/모험", "액션/어드벤쳐",
    "여행", "역사", "연예/오락", "연예오락", "연예정보", "영화",
    "오락", "외국어강좌", "외화 시리즈", "요리", "운동/건강",
    "의학/건강", "이용안내", "인물", "일일연속극", "자격증강좌",
    "자연", "주말연속극", "중등", "초등", "추리/미스터리", "축구",
    "코미디", "콘서트", "학습", "학원/순정/연애", "해외", "호러/공포",
]  # 67개

CT_CL_LIST = [
    "TV 시사/교양", "TV 연예/오락", "TV드라마", "TV애니메이션",
    "공연/음악", "교육", "기타", "다큐", "라이프", "미분류",
    "스포츠", "영화", "우리동네", "키즈",
]  # 14개

AGE_GRP_LIST = [
    "10대", "20대", "30대", "40대", "50대",
    "60대", "70대", "80대", "90대이상", "unknown",
]  # 10개 (마지막은 None/기타 처리용)
