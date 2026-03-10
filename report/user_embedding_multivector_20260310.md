# User Embedding 멀티벡터 구현 보고서

- **일시**: 2026-03-10
- **브랜치**: RAG_Pipeline_Design
- **작업 범위**: Phase 0~7 (설계서 §2.5 기반 448차원 멀티벡터 재설계)

---

## 작업 목표

기존 384차원 텍스트 임베딩을 설계서 §2.5 스펙에 맞게
`behavior(256) + genre_preference(128) + demographic(64) = 448차원` 멀티벡터로 재설계

---

## 완료 항목

### Phase 0: 기반 설정
| 항목 | 내용 |
|------|------|
| `config.py` 업데이트 | BEHAVIOR_DIM=256, GENRE_DIM=128, DEMOGRAPHIC_DIM=64, HYBRID_DIM=448 |
| GENRE_LIST | DB 실제값 67개 |
| CT_CL_LIST | DB 실제값 14개 |
| AGE_GRP_LIST | DB 실제값 9개 + unknown |
| DDL 생성 및 적용 | `Database_Design/schema/04_user_embedding_meta.sql` PostgreSQL 적용 완료 |

### Phase 1: feature_extractor 개선
- `extract_numeric_features()` 추가
  - 최근 90일 시청 이력 필터 (`strt_dt >= NOW() - INTERVAL '90 days'`)
  - 장르별 완주율·친화도 집계
  - 요일별(DOW) 시청 분포
  - 인구통계 (age_grp10, inhome_rate, svod_scrb_cnt_grp, paid_chnl_cnt_grp, ch_hh_avg_month1, kids_use_pv_month1, nfx_use_yn)
- **TDD**: 20/20 통과

### Phase 2: behavior_embedding.py (256차원)
- 장르별 완주율 (67차원)
- 장르별 친화도 (67차원, 정규화)
- 요일별 시청 분포 (7차원, 비율)
- 총 시청 수 스칼라 (1차원)
- 제로 패딩 → 256차원, L2 정규화
- **TDD**: 10/10 통과

### Phase 3: genre_embedding.py (128차원)
- 장르별 친화도 (67차원, 정규화)
- ct_cl 분포 비율 (14차원)
- 제로 패딩 → 128차원, L2 정규화
- **TDD**: 11/11 통과

### Phase 4: demographic_embedding.py (64차원)
- age_grp10 원핫 인코딩 (10차원)
- inhome_rate, nfx_use_yn, svod, paid_chnl, ch_hh, kids_pv 스칼라 (6차원)
- 제로 패딩 → 64차원, L2 정규화
- **TDD**: 13/13 통과

### Phase 5: multivector_embedding.py
- `build_hybrid_vector()`: behavior + genre + demographic concat → 448차원
- **TDD**: 16/16 통과

### Phase 6: pipeline.py 업데이트
- `run_all()`: 멀티벡터 파이프라인 (CHROMA_COLLECTION_V2)
- `run_single()`: 단일 사용자 멀티벡터 생성
- `user_embedding_meta` PostgreSQL 테이블에 메타 저장
- `--legacy` 옵션으로 구버전 384차원 텍스트 임베딩 유지

### Phase 7: 검증
- `python pipeline.py --limit 5` 실행 → 성공 5/5
- `user_embedding_meta` 테이블 5건 정상 저장 확인

---

## TDD 결과 총합

| 파일 | 테스트 수 | 결과 |
|------|----------|------|
| test_numeric_features.py | 20 | ✅ |
| test_behavior_embedding.py | 10 | ✅ |
| test_genre_embedding.py | 11 | ✅ |
| test_demographic_embedding.py | 13 | ✅ |
| test_multivector_embedding.py | 16 | ✅ |
| **합계** | **70** | **70/70** |

---

## 신규 파일 목록

| 파일 | 역할 |
|------|------|
| `user_embedding/behavior_embedding.py` | 행동 벡터 256차원 |
| `user_embedding/genre_embedding.py` | 장르 선호도 벡터 128차원 |
| `user_embedding/demographic_embedding.py` | 인구통계 벡터 64차원 |
| `user_embedding/multivector_embedding.py` | 448차원 하이브리드 벡터 |
| `user_embedding/test_numeric_features.py` | TDD 테스트 20개 |
| `user_embedding/test_behavior_embedding.py` | TDD 테스트 10개 |
| `user_embedding/test_genre_embedding.py` | TDD 테스트 11개 |
| `user_embedding/test_demographic_embedding.py` | TDD 테스트 13개 |
| `user_embedding/test_multivector_embedding.py` | TDD 테스트 16개 |
| `Database_Design/schema/04_user_embedding_meta.sql` | PostgreSQL DDL |

---

## 수정 파일

| 파일 | 변경 내용 |
|------|---------|
| `user_embedding/config.py` | 멀티벡터 상수, GENRE_LIST, CT_CL_LIST, AGE_GRP_LIST 추가 |
| `user_embedding/feature_extractor.py` | `extract_numeric_features()` 추가 |
| `user_embedding/pipeline.py` | 멀티벡터 파이프라인으로 전환 |

---

## DB 실제 컬럼 확인사항 (주의)

| 컬럼명 | 실제 타입 | 주의 |
|--------|----------|------|
| `svod_scrb_cnt_grp` | character varying | 숫자처럼 보이지만 문자열 |
| `paid_chnl_cnt_grp` | character varying | 숫자처럼 보이지만 문자열 |
| `ch_hh_avg_month1` | double precision | 설계서는 `ch_hh_month1` → 실제는 `ch_hh_avg_month1` |
| `strt_dt` | timestamp | 시청 시작 시각 (DOW 계산 기준) |

---

## 다음 단계

- [ ] `python pipeline.py --limit 10000` 중규모 실행 검증
- [ ] 시청 이력 날짜 범위 확인 (base_record_count=0 원인 파악)
- [ ] 전체 242,702명 임베딩 생성
- [ ] 유사 사용자 → VOD 추천 연동
- [ ] temporal_embedding (선택적) 추가 검토
