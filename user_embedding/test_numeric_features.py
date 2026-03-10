"""
TDD: extract_numeric_features() 테스트 (Red → Green)
Phase 1: 멀티벡터 임베딩용 수치 특징 추출 함수
"""
import unittest
from unittest.mock import MagicMock, patch, call
from feature_extractor import extract_numeric_features


SHA = "abc123"

# -- 공통 픽스처 ---------------------------------------------------------

def _genre_rows():
    """장르별 통계 쿼리 결과"""
    return [
        {"genre": "드라마",   "cnt": 15, "avg_cr": 0.75, "avg_sat": 0.80},
        {"genre": "영화",     "cnt": 10, "avg_cr": 0.60, "avg_sat": 0.70},
        {"genre": "애니메이션", "cnt":  5, "avg_cr": 0.90, "avg_sat": 0.85},
    ]

def _dow_rows():
    """요일별 시청 분포 쿼리 결과 (PostgreSQL EXTRACT(DOW): 0=일, 6=토)"""
    return [
        {"dow": 0, "cnt": 3},
        {"dow": 1, "cnt": 8},
        {"dow": 5, "cnt": 6},
        {"dow": 6, "cnt": 4},
    ]

def _user_row():
    """users 테이블 쿼리 결과"""
    return {
        "age_grp10":          "40대",
        "inhome_rate":        0.65,
        "svod_scrb_cnt_grp":  "2",
        "paid_chnl_cnt_grp":  "3",
        "ch_hh_avg_month1":   150.0,
        "kids_use_pv_month1": 10.0,
        "nfx_use_yn":         "Y",
    }

def _total_row():
    """총 시청 수 쿼리 결과"""
    return {"total": 30}


def _make_conn(genre_rows, dow_rows, user_row, total_row=None):
    """4번 fetchone/fetchall 호출 순서에 맞는 mock cursor 생성"""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)

    # fetchall: genre_rows → dow_rows
    cur.fetchall.side_effect = [genre_rows, dow_rows]
    # fetchone: total_row → user_row
    cur.fetchone.side_effect = [
        total_row if total_row is not None else {"total": 30},
        user_row,
    ]

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ── 테스트 클래스 ─────────────────────────────────────────────────────

class TestExtractNumericFeaturesStructure(unittest.TestCase):
    """반환값 구조 검증"""

    def setUp(self):
        self.conn, _ = _make_conn(_genre_rows(), _dow_rows(), _user_row())
        self.result = extract_numeric_features(self.conn, SHA)

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_has_genre_stats_key(self):
        self.assertIn("genre_stats", self.result)

    def test_has_dow_distribution_key(self):
        self.assertIn("dow_distribution", self.result)

    def test_has_total_watch_count_key(self):
        self.assertIn("total_watch_count", self.result)

    def test_has_user_demographic_keys(self):
        for key in ("age_grp10", "inhome_rate", "svod_scrb_cnt_grp",
                    "paid_chnl_cnt_grp", "ch_hh_avg_month1",
                    "kids_use_pv_month1", "nfx_use_yn"):
            with self.subTest(key=key):
                self.assertIn(key, self.result)


class TestExtractNumericFeaturesGenreStats(unittest.TestCase):
    """genre_stats 값 검증"""

    def setUp(self):
        self.conn, _ = _make_conn(_genre_rows(), _dow_rows(), _user_row())
        self.result = extract_numeric_features(self.conn, SHA)
        self.genre_stats = self.result["genre_stats"]

    def test_genre_stats_is_dict(self):
        self.assertIsInstance(self.genre_stats, dict)

    def test_genre_stats_contains_queried_genres(self):
        self.assertIn("드라마", self.genre_stats)
        self.assertIn("영화", self.genre_stats)

    def test_genre_entry_has_required_fields(self):
        drama = self.genre_stats["드라마"]
        for field in ("count", "avg_completion_rate", "avg_satisfaction", "affinity"):
            self.assertIn(field, drama)

    def test_genre_count_value(self):
        self.assertEqual(self.genre_stats["드라마"]["count"], 15)

    def test_genre_avg_completion_rate_value(self):
        self.assertAlmostEqual(self.genre_stats["드라마"]["avg_completion_rate"], 0.75)

    def test_genre_affinity_calculation(self):
        """affinity = count × avg_completion_rate × avg_satisfaction"""
        drama = self.genre_stats["드라마"]
        expected = 15 * 0.75 * 0.80
        self.assertAlmostEqual(drama["affinity"], expected, places=4)


class TestExtractNumericFeaturesDow(unittest.TestCase):
    """dow_distribution 값 검증"""

    def setUp(self):
        self.conn, _ = _make_conn(_genre_rows(), _dow_rows(), _user_row())
        self.result = extract_numeric_features(self.conn, SHA)
        self.dow = self.result["dow_distribution"]

    def test_dow_is_dict(self):
        self.assertIsInstance(self.dow, dict)

    def test_dow_keys_are_int(self):
        for k in self.dow:
            self.assertIsInstance(k, int)

    def test_dow_values_correct(self):
        self.assertEqual(self.dow[1], 8)
        self.assertEqual(self.dow[5], 6)


class TestExtractNumericFeaturesDemographic(unittest.TestCase):
    """인구통계 필드 타입 및 값 검증"""

    def setUp(self):
        self.conn, _ = _make_conn(_genre_rows(), _dow_rows(), _user_row())
        self.result = extract_numeric_features(self.conn, SHA)

    def test_age_grp10_value(self):
        self.assertEqual(self.result["age_grp10"], "40대")

    def test_inhome_rate_value(self):
        self.assertAlmostEqual(self.result["inhome_rate"], 0.65)

    def test_nfx_use_yn_value(self):
        self.assertEqual(self.result["nfx_use_yn"], "Y")

    def test_total_watch_count_value(self):
        self.assertEqual(self.result["total_watch_count"], 30)


class TestExtractNumericFeaturesEdgeCases(unittest.TestCase):
    """엣지 케이스 검증"""

    def test_empty_watch_history_returns_zero_total(self):
        conn, _ = _make_conn([], [], _user_row(), total_row={"total": 0})
        result = extract_numeric_features(conn, SHA)
        self.assertEqual(result["total_watch_count"], 0)
        self.assertEqual(result["genre_stats"], {})
        self.assertEqual(result["dow_distribution"], {})

    def test_none_user_row_returns_defaults(self):
        conn, _ = _make_conn(_genre_rows(), _dow_rows(), None)
        result = extract_numeric_features(conn, SHA)
        self.assertIsNone(result["age_grp10"])
        self.assertEqual(result["inhome_rate"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
