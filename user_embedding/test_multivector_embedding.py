"""
TDD: 멀티벡터 임베딩 통합 테스트 (Phase 5)
behavior(256) + genre(128) + demographic(64) = hybrid(448)
"""
import unittest
import numpy as np
from config import BEHAVIOR_DIM, GENRE_DIM, DEMOGRAPHIC_DIM, HYBRID_DIM, GENRE_LIST


def _full_numeric():
    """완전한 numeric 딕셔너리 (통합 테스트용)"""
    return {
        "genre_stats": {
            GENRE_LIST[0]: {"count": 20, "avg_completion_rate": 0.8, "avg_satisfaction": 0.85, "affinity": 13.6},
            GENRE_LIST[5]: {"count": 10, "avg_completion_rate": 0.6, "avg_satisfaction": 0.7, "affinity": 4.2},
        },
        "ct_cl_distribution": {"TV드라마": 15, "영화": 8},
        "dow_distribution": {1: 10, 3: 8, 6: 5},
        "total_watch_count": 30,
        "age_grp10":          "30대",
        "inhome_rate":        0.72,
        "svod_scrb_cnt_grp":  "1",
        "paid_chnl_cnt_grp":  "2",
        "ch_hh_avg_month1":   200.0,
        "kids_use_pv_month1": 0.0,
        "nfx_use_yn":         "N",
    }


class TestIndividualVectorDims(unittest.TestCase):
    """개별 벡터 차원 확인"""

    def setUp(self):
        from behavior_embedding import build_behavior_vector
        from genre_embedding import build_genre_vector
        from demographic_embedding import build_demographic_vector
        self.num = _full_numeric()
        self.bvec = build_behavior_vector(self.num)
        self.gvec = build_genre_vector(self.num)
        self.dvec = build_demographic_vector(self.num)

    def test_behavior_dim(self):
        self.assertEqual(self.bvec.shape[0], BEHAVIOR_DIM)

    def test_genre_dim(self):
        self.assertEqual(self.gvec.shape[0], GENRE_DIM)

    def test_demographic_dim(self):
        self.assertEqual(self.dvec.shape[0], DEMOGRAPHIC_DIM)


class TestHybridVector(unittest.TestCase):
    """hybrid = concat(behavior, genre, demographic) → 448차원"""

    def setUp(self):
        from behavior_embedding import build_behavior_vector
        from genre_embedding import build_genre_vector
        from demographic_embedding import build_demographic_vector
        self.num = _full_numeric()
        b = build_behavior_vector(self.num)
        g = build_genre_vector(self.num)
        d = build_demographic_vector(self.num)
        self.hybrid = np.concatenate([b, g, d])

    def test_hybrid_dim_is_448(self):
        self.assertEqual(self.hybrid.shape[0], HYBRID_DIM)

    def test_hybrid_dtype_float32(self):
        self.assertEqual(self.hybrid.dtype, np.float32)

    def test_hybrid_no_nan(self):
        self.assertFalse(np.isnan(self.hybrid).any())

    def test_hybrid_no_inf(self):
        self.assertFalse(np.isinf(self.hybrid).any())

    def test_behavior_slice_matches(self):
        from behavior_embedding import build_behavior_vector
        b = build_behavior_vector(self.num)
        np.testing.assert_array_equal(self.hybrid[:BEHAVIOR_DIM], b)

    def test_genre_slice_matches(self):
        from genre_embedding import build_genre_vector
        g = build_genre_vector(self.num)
        np.testing.assert_array_equal(
            self.hybrid[BEHAVIOR_DIM:BEHAVIOR_DIM + GENRE_DIM], g
        )

    def test_demographic_slice_matches(self):
        from demographic_embedding import build_demographic_vector
        d = build_demographic_vector(self.num)
        np.testing.assert_array_equal(
            self.hybrid[BEHAVIOR_DIM + GENRE_DIM:], d
        )


class TestBuildHybridFunction(unittest.TestCase):
    """build_hybrid_vector() 함수 테스트"""

    def setUp(self):
        from multivector_embedding import build_hybrid_vector
        self.build = build_hybrid_vector
        self.num = _full_numeric()

    def test_returns_numpy_array(self):
        vec = self.build(self.num)
        self.assertIsInstance(vec, np.ndarray)

    def test_dim_448(self):
        vec = self.build(self.num)
        self.assertEqual(vec.shape[0], HYBRID_DIM)

    def test_dtype_float32(self):
        vec = self.build(self.num)
        self.assertEqual(vec.dtype, np.float32)

    def test_no_nan(self):
        vec = self.build(self.num)
        self.assertFalse(np.isnan(vec).any())

    def test_empty_input_still_works(self):
        empty = {
            "genre_stats": {}, "ct_cl_distribution": {}, "dow_distribution": {},
            "total_watch_count": 0,
            "age_grp10": None, "inhome_rate": 0.0, "svod_scrb_cnt_grp": None,
            "paid_chnl_cnt_grp": None, "ch_hh_avg_month1": 0.0,
            "kids_use_pv_month1": 0.0, "nfx_use_yn": None,
        }
        vec = self.build(empty)
        self.assertEqual(vec.shape[0], HYBRID_DIM)

    def test_different_users_different_vectors(self):
        num2 = _full_numeric()
        num2["age_grp10"] = "70대"
        num2["inhome_rate"] = 0.1
        num2["genre_stats"] = {}
        v1 = self.build(self.num)
        v2 = self.build(num2)
        self.assertFalse(np.allclose(v1, v2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
