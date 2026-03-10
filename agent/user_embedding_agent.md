# User Embedding Agent

## 개요
- **이름**: User Embedding Agent
- **슬래시 커맨드**: `/user-embedding`
- **목적**: 사용자 시청 이력 기반 임베딩 생성 및 유사 사용자 검색
- **개발 방법론**: TDD
- **출력**: `report/user_embedding_report_YYYYMMDD.md`

## 커맨드 파일 위치
`.claude/commands/user-embedding.md`

## 모듈 구조
```
user_embedding/
├── config.py              ← 설정 (DB, 임베딩 모델, ChromaDB 경로)
├── feature_extractor.py   ← 사용자 특징 추출 (watch_history + users)
├── embedding.py           ← sentence-transformers 임베딩 생성
├── vector_store.py        ← ChromaDB 벡터 저장/검색
├── pipeline.py            ← 메인 파이프라인
├── test_feature_extractor.py  ← TDD 테스트
└── test_embedding.py          ← TDD 테스트
```

## 사용법
```bash
cd user_embedding

# 전체 사용자 임베딩 생성 (242,702명)
python pipeline.py

# 일부만 테스트
python pipeline.py --limit 1000

# 특정 사용자 임베딩 생성
python pipeline.py --user <sha2_hash>

# 유사 사용자 검색
python pipeline.py --find <sha2_hash> --top-k 10
```

## 기술 스택
| 항목 | 선택 | 이유 |
|------|------|------|
| 임베딩 모델 | all-MiniLM-L6-v2 | 경량, 384차원, 한국어 지원 |
| 벡터 DB | ChromaDB | Python 순수 구현, 설치 간편 |
| 특징 추출 | SQL + 자연어 변환 | 사용자 특성 + 시청 이력 통합 |

## 사용자 특징 구성
- 연령대 (age_grp10)
- 선호 장르 Top 3 (watch_history × vods join)
- 선호 콘텐츠 타입 Top 2
- 평균 만족도 / 평균 완료율
- 총 시청 수
- 재택 시청 비율 (inhome_rate)
- 넷플릭스 이용 여부 (nfx_use_yn)
- 키즈 콘텐츠 이용 여부

## 테스트 현황
- test_feature_extractor.py: 10개 테스트 통과
- test_embedding.py: 10개 테스트 통과
- 총 20/20 통과

## 생성 일자
2026-03-10
