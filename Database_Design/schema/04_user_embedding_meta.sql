-- ============================================================
-- user_embedding_meta: 사용자 임베딩 메타 테이블
-- 설계서 §2.5 기반 멀티벡터 임베딩 추적
-- PostgreSQL 18
-- ============================================================

CREATE TABLE IF NOT EXISTS user_embedding_meta (
    id                    BIGSERIAL PRIMARY KEY,
    sha2_hash             VARCHAR(64)  NOT NULL
                              REFERENCES users(sha2_hash) ON DELETE CASCADE,
    embedding_type        VARCHAR(32)  NOT NULL,          -- 'BEHAVIOR' | 'GENRE' | 'DEMOGRAPHIC' | 'HYBRID'
    embedding_dimension   INTEGER      NOT NULL,
    embedding_model       VARCHAR(64)  NOT NULL DEFAULT 'numeric_composite_v1',
    base_record_count     INTEGER,                        -- 사용된 watch_history 건수
    watch_history_days    INTEGER      NOT NULL DEFAULT 90,
    created_at            TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at            TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

    CONSTRAINT uq_user_embedding_type UNIQUE (sha2_hash, embedding_type),
    CONSTRAINT chk_embedding_type
        CHECK (embedding_type IN ('BEHAVIOR', 'GENRE', 'DEMOGRAPHIC', 'HYBRID')),
    CONSTRAINT chk_embedding_dimension
        CHECK (embedding_dimension > 0),
    CONSTRAINT chk_watch_history_days
        CHECK (watch_history_days > 0)
);

-- updated_at 자동 갱신 트리거 함수
CREATE OR REPLACE FUNCTION update_user_embedding_meta_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 등록
DROP TRIGGER IF EXISTS trg_user_embedding_meta_updated_at ON user_embedding_meta;
CREATE TRIGGER trg_user_embedding_meta_updated_at
    BEFORE UPDATE ON user_embedding_meta
    FOR EACH ROW
    EXECUTE FUNCTION update_user_embedding_meta_updated_at();

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_user_embedding_meta_sha2
    ON user_embedding_meta (sha2_hash);

CREATE INDEX IF NOT EXISTS idx_user_embedding_meta_type
    ON user_embedding_meta (embedding_type);

CREATE INDEX IF NOT EXISTS idx_user_embedding_meta_updated
    ON user_embedding_meta (updated_at DESC);
