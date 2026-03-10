# User Embedding

사용자 임베딩 파이프라인을 실행하거나 유사 사용자를 검색합니다.

## 역할
- 사용자의 시청 이력과 프로필을 분석하여 임베딩 벡터 생성
- ChromaDB에 저장하여 유사 사용자 검색에 활용
- TDD 원칙 준수: 코드 변경 시 테스트 먼저 작성

## 작업 디렉토리
`user_embedding/`

## 실행 방법

```bash
# 1. 테스트 먼저 확인
cd user_embedding
python -m pytest test_feature_extractor.py test_embedding.py -v

# 2. 소규모 테스트 실행
python pipeline.py --limit 100

# 3. 전체 실행
python pipeline.py

# 4. 특정 사용자 임베딩 + 유사 사용자 검색
python pipeline.py --user <sha2_hash>
python pipeline.py --find <sha2_hash> --top-k 10
```

## 작업 완료 시
- `report/user_embedding_report_YYYYMMDD_HHMMSS.md` 에 결과 보고서 저장
- 보고서 포함 항목: 처리 사용자 수, 임베딩 차원, 소요 시간, 샘플 유사 사용자 결과

## 주요 파일
| 파일 | 역할 |
|------|------|
| `config.py` | DB, 모델, ChromaDB 설정 |
| `feature_extractor.py` | 사용자 특징 추출 |
| `embedding.py` | 임베딩 생성 (all-MiniLM-L6-v2) |
| `vector_store.py` | ChromaDB 저장/검색 |
| `pipeline.py` | 메인 실행 파일 |

$ARGUMENTS
