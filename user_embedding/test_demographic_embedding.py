"""
TDD: demographic_embedding.py 테스트 (Red → Green)
Phase 4: 인구통계 벡터 64차원
"""
import unittest
import numpy as np
from config import DEMOGRAPHIC_DIM, AGE_GRP_LIST


def _make_numeric(**kwargs):
    defaults = {
        "age_grp10":          "40대",
        "inhome_rate":        0.65,
        "svod_scrb_cnt_grp":  "2",
        "paid_chnl_cnt_grp":  "3",
        "ch_hh_avg_month1":   150.0,
        "kids_use_pv_month1": 10.0,
        "nfx_use_yn":         "Y",
    }
    defaults.update(kwargs)
    return defaults


class TestDemographicEmbeddingDim(unittest.TestCase):

    def setUp(self):
        from demographic_embedding import build_demographic_vector
        self.build = build_demographic_vector

    def test_output_is_numpy_array(self):
        vec = self.build(_make_numeric())
        self.assertIsInstance(vec, np.ndarray)

    def test_output_dim_is_64(self):
        vec = self.build(_make_numeric())
        self.assertEqual(vec.shape[0], DEMOGRAPHIC_DIM)

    def test_output_dtype_float32(self):
        vec = self.build(_make_numeric())
        self.assertEqual(vec.dtype, np.float32)

    def test_none_values_return_valid_vector(self):
        vec = self.build(_make_numeric(age_grp10=None, nfx_use_yn=None,
                                        svod_scrb_cnt_grp=None, paid_chnl_cnt_grp=None))
        self.assertEqual(vec.shape[0], DEMOGRAPHIC_DIM)

    def test_no_nan(self):
        vec = self.build(_make_numeric())
        self.assertFalse(np.isnan(vec).any())

    def test_no_inf(self):
        vec = self.build(_make_numeric())
        self.assertFalse(np.isinf(vec).any())


class TestDemographicEmbeddingNorm(unittest.TestCase):

    def setUp(self):
        from demographic_embedding import build_demographic_vector
        self.build = build_demographic_vector

    def test_l2_norm_positive(self):
        vec = self.build(_make_numeric())
        self.assertGreater(np.linalg.norm(vec), 0)

    def test_values_bounded_after_l2_norm(self):
        vec = self.build(_make_numeric())
        self.assertTrue((np.abs(vec) <= 1.0 + 1e-6).all())


class TestDemographicEmbeddingContent(unittest.TestCase):

    def setUp(self):
        from demographic_embedding import build_demographic_vector
        self.build = build_demographic_vector

    def test_age_group_affects_vector(self):
        v1 = self.build(_make_numeric(age_grp10="20대"))
        v2 = self.build(_make_numeric(age_grp10="60대"))
        self.assertFalse(np.allclose(v1, v2))

    def test_nfx_yn_affects_vector(self):
        v1 = self.build(_make_numeric(nfx_use_yn="Y"))
        v2 = self.build(_make_numeric(nfx_use_yn="N"))
        self.assertFalse(np.allclose(v1, v2))

    def test_inhome_rate_affects_vector(self):
        v1 = self.build(_make_numeric(inhome_rate=0.1))
        v2 = self.build(_make_numeric(inhome_rate=0.9))
        self.assertFalse(np.allclose(v1, v2))

    def test_same_input_same_vector(self):
        n = _make_numeric()
        np.testing.assert_array_equal(self.build(n), self.build(n))

    def test_unknown_age_group_handled(self):
        """AGE_GRP_LIST에 없는 값도 처리 가능 (unknown 버킷)"""
        vec = self.build(_make_numeric(age_grp10="알수없음"))
        self.assertEqual(vec.shape[0], DEMOGRAPHIC_DIM)


if __name__ == "__main__":
    unittest.main(verbosity=2)
