"""
TDD: behavior_embedding.py 테스트 (Red → Green)
Phase 2: 행동 벡터 256차원
"""
import unittest
import numpy as np
from config import BEHAVIOR_DIM, GENRE_LIST


class TestBehaviorEmbeddingDim(unittest.TestCase):
    """출력 차원 검증"""

    def _make_numeric(self, n_genres=3, with_dow=True):
        genre_stats = {
            GENRE_LIST[i]: {
                "count": (i + 1) * 5,
                "avg_completion_rate": 0.5 + i * 0.1,
                "avg_satisfaction": 0.6 + i * 0.05,
                "affinity": (i + 1) * 5 * (0.5 + i * 0.1) * (0.6 + i * 0.05),
            }
            for i in range(n_genres)
        }
        dow_distribution = {i: (i + 1) * 2 for i in range(7)} if with_dow else {}
        return {
            "genre_stats": genre_stats,
            "dow_distribution": dow_distribution,
            "total_watch_count": 50,
        }

    def setUp(self):
        from behavior_embedding import build_behavior_vector
        self.build = build_behavior_vector

    def test_output_is_numpy_array(self):
        vec = self.build(self._make_numeric())
        self.assertIsInstance(vec, np.ndarray)

    def test_output_dim_is_256(self):
        vec = self.build(self._make_numeric())
        self.assertEqual(vec.shape[0], BEHAVIOR_DIM)

    def test_output_dtype_float32(self):
        vec = self.build(self._make_numeric())
        self.assertEqual(vec.dtype, np.float32)

    def test_all_genres_zero_returns_valid_vector(self):
        numeric = {"genre_stats": {}, "dow_distribution": {}, "total_watch_count": 0}
        vec = self.build(numeric)
        self.assertEqual(vec.shape[0], BEHAVIOR_DIM)

    def test_no_nan_in_output(self):
        vec = self.build(self._make_numeric())
        self.assertFalse(np.isnan(vec).any())

    def test_no_inf_in_output(self):
        vec = self.build(self._make_numeric())
        self.assertFalse(np.isinf(vec).any())


class TestBehaviorEmbeddingNorm(unittest.TestCase):
    """정규화 검증"""

    def _make_numeric(self):
        return {
            "genre_stats": {
                GENRE_LIST[0]: {
                    "count": 20, "avg_completion_rate": 0.8,
                    "avg_satisfaction": 0.9, "affinity": 14.4,
                },
            },
            "dow_distribution": {1: 10, 3: 5},
            "total_watch_count": 25,
        }

    def setUp(self):
        from behavior_embedding import build_behavior_vector
        self.build = build_behavior_vector

    def test_l2_norm_is_positive(self):
        vec = self.build(self._make_numeric())
        norm = float(np.linalg.norm(vec))
        self.assertGreater(norm, 0)

    def test_values_in_reasonable_range(self):
        """L2 정규화 후 각 요소 절댓값 ≤ 1"""
        vec = self.build(self._make_numeric())
        self.assertTrue((np.abs(vec) <= 1.0 + 1e-6).all())


class TestBehaviorEmbeddingContent(unittest.TestCase):
    """벡터 내용 검증: 시청 많은 장르가 반영되는지"""

    def setUp(self):
        from behavior_embedding import build_behavior_vector
        self.build = build_behavior_vector

    def test_different_inputs_produce_different_vectors(self):
        n1 = {
            "genre_stats": {GENRE_LIST[0]: {"count": 30, "avg_completion_rate": 0.9, "avg_satisfaction": 0.9, "affinity": 24.3}},
            "dow_distribution": {1: 20},
            "total_watch_count": 30,
        }
        n2 = {
            "genre_stats": {GENRE_LIST[5]: {"count": 5, "avg_completion_rate": 0.2, "avg_satisfaction": 0.3, "affinity": 0.3}},
            "dow_distribution": {6: 5},
            "total_watch_count": 5,
        }
        v1 = self.build(n1)
        v2 = self.build(n2)
        self.assertFalse(np.allclose(v1, v2))

    def test_same_input_produces_same_vector(self):
        numeric = {
            "genre_stats": {GENRE_LIST[2]: {"count": 10, "avg_completion_rate": 0.7, "avg_satisfaction": 0.75, "affinity": 5.25}},
            "dow_distribution": {2: 7, 4: 3},
            "total_watch_count": 10,
        }
        v1 = self.build(numeric)
        v2 = self.build(numeric)
        np.testing.assert_array_equal(v1, v2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
