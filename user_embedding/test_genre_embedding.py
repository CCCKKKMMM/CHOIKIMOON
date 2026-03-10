"""
TDD: genre_embedding.py 테스트 (Red → Green)
Phase 3: 장르 선호도 벡터 128차원
"""
import unittest
import numpy as np
from config import GENRE_DIM, GENRE_LIST, CT_CL_LIST


def _make_numeric(genre_affinities=None, ct_cl_counts=None):
    genre_stats = {}
    for g, aff in (genre_affinities or {}).items():
        genre_stats[g] = {"count": 10, "avg_completion_rate": 0.7, "avg_satisfaction": 0.8, "affinity": aff}
    return {
        "genre_stats": genre_stats,
        "ct_cl_distribution": ct_cl_counts or {},
    }


class TestGenreEmbeddingDim(unittest.TestCase):

    def setUp(self):
        from genre_embedding import build_genre_vector
        self.build = build_genre_vector

    def test_output_is_numpy_array(self):
        vec = self.build(_make_numeric({GENRE_LIST[0]: 5.0}))
        self.assertIsInstance(vec, np.ndarray)

    def test_output_dim_is_128(self):
        vec = self.build(_make_numeric({GENRE_LIST[0]: 5.0}))
        self.assertEqual(vec.shape[0], GENRE_DIM)

    def test_output_dtype_float32(self):
        vec = self.build(_make_numeric({GENRE_LIST[0]: 5.0}))
        self.assertEqual(vec.dtype, np.float32)

    def test_empty_input_returns_valid_vector(self):
        vec = self.build(_make_numeric())
        self.assertEqual(vec.shape[0], GENRE_DIM)

    def test_no_nan(self):
        vec = self.build(_make_numeric({GENRE_LIST[3]: 2.5}))
        self.assertFalse(np.isnan(vec).any())

    def test_no_inf(self):
        vec = self.build(_make_numeric({GENRE_LIST[3]: 2.5}))
        self.assertFalse(np.isinf(vec).any())


class TestGenreEmbeddingNorm(unittest.TestCase):

    def setUp(self):
        from genre_embedding import build_genre_vector
        self.build = build_genre_vector

    def test_l2_norm_positive_for_nonzero_input(self):
        vec = self.build(_make_numeric({GENRE_LIST[1]: 8.0, GENRE_LIST[4]: 3.0}))
        self.assertGreater(np.linalg.norm(vec), 0)

    def test_values_bounded_after_l2_norm(self):
        vec = self.build(_make_numeric({GENRE_LIST[0]: 100.0}))
        self.assertTrue((np.abs(vec) <= 1.0 + 1e-6).all())


class TestGenreEmbeddingContent(unittest.TestCase):

    def setUp(self):
        from genre_embedding import build_genre_vector
        self.build = build_genre_vector

    def test_different_genre_affinities_different_vectors(self):
        v1 = self.build(_make_numeric({GENRE_LIST[0]: 10.0}))
        v2 = self.build(_make_numeric({GENRE_LIST[10]: 10.0}))
        self.assertFalse(np.allclose(v1, v2))

    def test_same_input_same_vector(self):
        numeric = _make_numeric({GENRE_LIST[2]: 7.0, GENRE_LIST[6]: 4.0},
                                 ct_cl_counts={"TV드라마": 15, "영화": 5})
        v1 = self.build(numeric)
        v2 = self.build(numeric)
        np.testing.assert_array_equal(v1, v2)

    def test_ct_cl_distribution_included(self):
        """ct_cl 분포 있을 때와 없을 때 벡터가 달라야 함"""
        v1 = self.build(_make_numeric({GENRE_LIST[0]: 5.0}, ct_cl_counts={"TV드라마": 20}))
        v2 = self.build(_make_numeric({GENRE_LIST[0]: 5.0}, ct_cl_counts={}))
        self.assertFalse(np.allclose(v1, v2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
