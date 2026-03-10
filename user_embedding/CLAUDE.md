# User Embedding 모듈 개발 지침

## 목적
사용자 시청 이력 기반 임베딩 벡터 생성 → 유사 사용자 검색 → VOD 추천에 활용

---

## 설계 문서 기반 스펙 (Database_Design 브랜치)

### 참조 문서
- `Database_Design/.claude/skills/VOD_RECOMMENDATION_LOGICAL_SCHEMA.md`
- `Database_Design/.claude/skills/SATISFACTION_FORMULA_UPDATE.md`

### USER_EMBEDDING 엔티티 설계 (설계서 §2.5)
```
user_embedding = concat(
    behavior_embedding(completion_rates, watch_frequency),     → 256차원
    genre_preference_embedding(genre_affinity_scores),         → 128차원
    demographic_embedding(age_grp10, gender, inhome_rate),     → 64차원
    temporal_embedding(seasonality, time_of_day_preference)    → (선택)
)
최종 복합 벡터: 448차원 (현재 구현: 384차원 text embedding → 재설계 필요)
```

### 사용자 벡터 생성 파이프라인 (설계서 §4.2)
```
WATCH_HISTORY 조회 (최근 90일)
    ↓
[통계 계산]
    ├─ 장르별 완주율 집계
    ├─ 시청 빈도 분포
    └─ 시간대별 선호도
    ↓
[벡터 생성] ← 분리된 3개 임베딩 생성
    ├─ behavior_embedding: 완주율 + 시청 빈도 (256차원)
    ├─ genre_preference_embedding: 장르별 친화도 (128차원)
    ├─ demographic_embedding: 연령 + 성별 + 행동율 (64차원)
    └─ (temporal_embedding: 요일/시간대 선호 - optional)
    ↓
벡터 정규화 (L2 Norm)
    ↓
ChromaDB 저장 (벡터) + PostgreSQL user_embedding 메타 테이블 저장
```

### 만족도(Satisfaction) 공식 (설계서 §9.2 + SATISFACTION_FORMULA_UPDATE.md)
```
satisfaction = (v * R + m * C) / (v + m)

- v: 영상별 시청 건수
- R: 시청 비율 (use_tms / disp_rtm, 0~1)
- C: 전체 평균 시청 비율 (global average)
- m: 신뢰도 파라미터 (기본값 5.0)
- 60초 이하 시청 → 0점 처리
```

---

## 현재 구현 vs 설계서 차이점

| 항목 | 설계서 스펙 | 현재 구현 | 조치 |
|------|-----------|---------|------|
| 임베딩 차원 | 448차원 (멀티벡터) | 384차원 (단일 텍스트) | 재설계 필요 |
| 임베딩 방식 | 구조화 수치벡터 분리 | 텍스트→sentence-transformer | 멀티벡터로 전환 |
| 벡터 DB | Milvus | ChromaDB | ChromaDB 유지 (개발 단계) |
| 메타 저장 | user_embedding 테이블 | 미생성 | DDL 작성 필요 |
| 시간대 임베딩 | 선택적 | 미구현 | 나중에 추가 |

---

## 실제 DB 환경 (주의사항)

- **DB**: PostgreSQL 18 (MySQL 아님)
- 설계서의 DDL은 MySQL 문법 → PostgreSQL로 변환 필요
  - `ENGINE=InnoDB` → 제거
  - `AUTO_INCREMENT` → `BIGSERIAL` 또는 `GENERATED ALWAYS AS IDENTITY`
  - `DATE_SUB(NOW(), INTERVAL 30 DAY)` → `NOW() - INTERVAL '30 days'`
  - `ON UPDATE CURRENT_TIMESTAMP` → 트리거로 구현
  - `FULLTEXT INDEX` → `GIN` + `to_tsvector`

---

## 개발 방식

- **TDD 필수**: 테스트 먼저 작성 → 구현 → 통과 확인
- **보고서**: 작업 완료 시 `../report/` 폴더에 저장
- **에이전트**: 에이전트 생성 시 `../agent/` 폴더에 저장

---

## 모듈 구조 (목표)

```
user_embedding/
├── CLAUDE.md                      ← 이 파일
├── config.py                      ← 설정
├── feature_extractor.py           ← 사용자 특징 추출 (SQL)
├── behavior_embedding.py          ← 행동 벡터 (256차원) [신규]
├── genre_embedding.py             ← 장르 선호도 벡터 (128차원) [신규]
├── demographic_embedding.py       ← 인구통계 벡터 (64차원) [신규]
├── embedding.py                   ← 단일 텍스트 임베딩 (현재, 유지)
├── vector_store.py                ← ChromaDB 저장/검색
├── pipeline.py                    ← 메인 파이프라인
└── test_*.py                      ← TDD 테스트
```

---

## user_embedding PostgreSQL 메타 테이블 (DDL)

```sql
CREATE TABLE user_embedding_meta (
    id                    BIGSERIAL PRIMARY KEY,
    sha2_hash             VARCHAR(64) NOT NULL REFERENCES users(sha2_hash) ON DELETE CASCADE,
    embedding_type        VARCHAR(32) NOT NULL,  -- 'BEHAVIOR', 'GENRE', 'DEMOGRAPHIC', 'HYBRID'
    embedding_dimension   INTEGER NOT NULL,
    embedding_model       VARCHAR(64) NOT NULL,
    base_record_count     INTEGER,               -- 사용된 watch_history 건수
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW(),
    UNIQUE (sha2_hash, embedding_type)
);
```

---

## 벡터 생성 상세 스펙

### behavior_embedding (256차원)
- 입력: 장르별 completion_rate, 시청 빈도
- 방법: 수치 벡터를 PCA/정규화로 256차원으로 맞춤
- 갱신: 주 1회

### genre_preference_embedding (128차원)
- 입력: 각 장르의 (시청 횟수 × 평균 만족도) 가중 합산
- 방법: 장르 원핫 인코딩 후 가중 평균, 128차원으로 패딩/축소
- 갱신: 주 1회

### demographic_embedding (64차원)
- 입력: age_grp10, inhome_rate, svod_scrb_cnt_grp, nfx_use_yn 등
- 방법: 카테고리 → 원핫, 수치 → 정규화, concatenate → 64차원
- 갱신: 월 1회
