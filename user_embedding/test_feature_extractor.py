"""
TDD: 사용자 특징 추출 테스트 (Red → Green → Refactor)
"""

import unittest
from unittest.mock import MagicMock
from feature_extractor import build_user_feature_text, extract_user_features


class TestBuildUserFeatureText(unittest.TestCase):
    """사용자 특징을 텍스트로 변환하는 함수 테스트"""

    def _sample_user(self, **kwargs):
        base = {
            "sha2_hash": "abc123",
            "age_grp10": "30대",
            "inhome_rate": 0.7,
            "svod_scrb_cnt_grp": "2",
            "paid_chnl_cnt_grp": "3",
            "ch_hh_avg_month1": 120.5,
            "kids_use_pv_month1": 0.0,
            "nfx_use_yn": "Y",
        }
        base.update(kwargs)
        return base

    def _sample_history(self):
        return {
            "avg_satisfaction": 3.8,
            "avg_completion_rate": 0.72,
            "total_watch_count": 45,
            "top_genres": ["드라마", "영화", "예능"],
            "top_ct_cls": ["TV드라마", "영화"],
        }

    def test_returns_string(self):
        text = build_user_feature_text(self._sample_user(), self._sample_history())
        self.assertIsInstance(text, str)

    def test_contains_age_group(self):
        text = build_user_feature_text(self._sample_user(age_grp10="40대"), self._sample_history())
        self.assertIn("40대", text)

    def test_contains_top_genres(self):
        text = build_user_feature_text(self._sample_user(), self._sample_history())
        self.assertIn("드라마", text)

    def test_contains_nfx_info(self):
        text = build_user_feature_text(self._sample_user(nfx_use_yn="Y"), self._sample_history())
        self.assertIn("넷플릭스", text)

    def test_no_nfx_when_n(self):
        text = build_user_feature_text(self._sample_user(nfx_use_yn="N"), self._sample_history())
        self.assertNotIn("넷플릭스", text)

    def test_contains_satisfaction(self):
        text = build_user_feature_text(self._sample_user(), self._sample_history())
        self.assertIn("3.8", text)

    def test_handles_null_age(self):
        text = build_user_feature_text(self._sample_user(age_grp10=None), self._sample_history())
        self.assertIsInstance(text, str)

    def test_not_empty(self):
        text = build_user_feature_text(self._sample_user(), self._sample_history())
        self.assertGreater(len(text), 10)


class TestExtractUserFeatures(unittest.TestCase):
    """DB에서 사용자 특징 추출 테스트 (mock 사용)"""

    def _make_mock_conn(self, fetchall_side_effect=None):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        mock_cursor.fetchone.return_value = {
            "avg_satisfaction": 3.5,
            "avg_completion_rate": 0.65,
            "total_watch_count": 30,
        }
        mock_cursor.fetchall.side_effect = fetchall_side_effect or [
            [{"genre": "드라마", "cnt": 20}, {"genre": "영화", "cnt": 10}],
            [{"ct_cl": "TV드라마", "cnt": 15}],
        ]
        return mock_conn

    def test_returns_dict_with_required_keys(self):
        result = extract_user_features(self._make_mock_conn(), "abc123")
        self.assertIn("avg_satisfaction", result)
        self.assertIn("avg_completion_rate", result)
        self.assertIn("total_watch_count", result)
        self.assertIn("top_genres", result)
        self.assertIn("top_ct_cls", result)

    def test_top_genres_is_list(self):
        result = extract_user_features(self._make_mock_conn(fetchall_side_effect=[[], []]), "abc123")
        self.assertIsInstance(result["top_genres"], list)
        self.assertIsInstance(result["top_ct_cls"], list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
