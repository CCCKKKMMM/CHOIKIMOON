# CHOIKIMOON 프로젝트

## 프로젝트 개요
VOD 추천 웹서비스 개발 프로젝트. 현재 Database 설계 및 RAG 파이프라인 구축 단계.

- **DB**: PostgreSQL (`choikimoon` 데이터베이스)
- **주요 데이터**: users(242,702명), vods(166,159편), watch_history(3,992,530건)

## 개발 방법론
**TDD (테스트 주도 개발)**을 따른다.
1. 테스트 코드 먼저 작성 (Red)
2. 구현 (Green)
3. 리팩토링 (Refactor)

## 폴더 구조
```
CHOIKIMOON/
├── Database_Design/
│   ├── migration/     ← CSV → PostgreSQL 마이그레이션
│   ├── rag/           ← RAG 파이프라인 (TMDB + Ollama)
│   └── schema/        ← SQL DDL 스크립트
├── RAG_Pipeline_Design/
├── report/            ← 작업 완료 후 보고서 저장
└── agent/             ← 에이전트 명세 저장
```

## 작업 규칙
- 작업이 끝나면 `report/` 폴더에 작업 내역 보고서를 저장한다.
- 에이전트를 만들면 `agent/` 폴더에 에이전트 명세를 저장한다.
- 슬래시 커맨드는 `.claude/commands/`에 저장한다.

## 기술 스택
- **언어**: Python
- **DB**: PostgreSQL + psycopg2
- **RAG 데이터 소스**: TMDB API (1순위), Ollama 로컬 LLM (2순위 폴백)
- **로컬 LLM**: Ollama v0.17.7
  - 설치 경로: `C:\Users\user\AppData\Local\Programs\Ollama\ollama.exe`
  - bash에서 사용 시: `/c/Users/user/AppData/Local/Programs/Ollama/ollama.exe`
  - 설정 모델: `llama3.2`

## 핵심 스키마
- `users` PK: `sha2_hash`
- `vods` PK: `full_asset_id`
- `watch_history` PK: `BIGSERIAL id`, FK: ON DELETE RESTRICT
- RAG 추적 컬럼: `rag_processed`, `rag_source`, `rag_processed_at`

## RAG 결측치 현황 (파일럿 테스트 후, 2026-03-10)
| 컬럼 | 결측 수 | 비고 |
|------|--------|------|
| smry | 7건 | TMDB 미등록 콘텐츠 |
| director | 17,726건 | 중국 드라마 위주, TMDB 커버리지 없음 |
| series_nm | 431건 | 영화·미분류 → 원래 없는 게 정상 |

### RAG 파이프라인 누적 결과
- TMDB 채움: 1,317건 (clean_title 적용 후 +50% 향상)
- 스킵 (정보 없음): 3,267건
- 미처리: 161,575건 (결측치가 거의 없어 우선순위 낮음)

## 환경변수
- `TMDB_API_KEY`: TMDB API 키 (필수)

## User Embedding 현황 (2026-03-10)
- 448차원 멀티벡터: behavior(256) + genre(128) + demographic(64)
- TDD: 70/70 테스트 통과
- 벡터 DB: ChromaDB (`user_embeddings_v2` 컬렉션)
- PG 메타: `user_embedding_meta` 테이블

## 커스텀 슬래시 커맨드
| 커맨드 | 설명 |
|--------|------|
| `/security-editor [경로]` | 보안 취약점 탐지 → 테스트 작성 → 수정 (OWASP Top 10) |
| `/user-embedding` | 사용자 임베딩 생성/검색 파이프라인 |
