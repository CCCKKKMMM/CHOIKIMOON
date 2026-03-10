"""
TDD: 임베딩 생성 및 벡터 저장소 테스트
"""

import unittest
from embedding import generate_embedding, EmbeddingModel
from vector_store import UserVectorStore


class TestEmbeddingModel(unittest.TestCase):
    """임베딩 생성 테스트"""

    @classmethod
    def setUpClass(cls):
        cls.model = EmbeddingModel()

    def test_returns_list(self):
        vec = generate_embedding("30대 드라마 선호 사용자", self.model)
        self.assertIsInstance(vec, list)

    def test_correct_dimension(self):
        from config import EMBEDDING_DIM
        vec = generate_embedding("테스트 사용자", self.model)
        self.assertEqual(len(vec), EMBEDDING_DIM)

    def test_different_texts_different_vectors(self):
        vec1 = generate_embedding("드라마를 좋아하는 30대 여성", self.model)
        vec2 = generate_embedding("액션영화를 좋아하는 20대 남성", self.model)
        self.assertNotEqual(vec1, vec2)

    def test_same_text_same_vector(self):
        text = "동일한 텍스트"
        vec1 = generate_embedding(text, self.model)
        vec2 = generate_embedding(text, self.model)
        self.assertEqual(vec1, vec2)

    def test_empty_string_handled(self):
        vec = generate_embedding("", self.model)
        self.assertEqual(len(vec), 384)


class TestUserVectorStore(unittest.TestCase):
    """ChromaDB 벡터 저장소 테스트"""

    @classmethod
    def setUpClass(cls):
        cls.store = UserVectorStore(path="./test_chroma_db", collection="test_users")

    def test_add_and_get(self):
        self.store.upsert("user_001", [0.1] * 384, {"age": "30대"})
        result = self.store.get("user_001")
        self.assertIsNotNone(result)

    def test_upsert_overwrites(self):
        self.store.upsert("user_002", [0.1] * 384, {"age": "20대"})
        self.store.upsert("user_002", [0.2] * 384, {"age": "20대"})
        result = self.store.get("user_002")
        self.assertIsNotNone(result)

    def test_find_similar_returns_list(self):
        self.store.upsert("user_003", [0.3] * 384, {"age": "30대"})
        results = self.store.find_similar([0.3] * 384, top_k=3)
        self.assertIsInstance(results, list)

    def test_find_similar_top_k(self):
        for i in range(5):
            self.store.upsert(f"user_10{i}", [float(i) / 10] * 384, {"idx": str(i)})
        results = self.store.find_similar([0.1] * 384, top_k=3)
        self.assertLessEqual(len(results), 3)

    def test_count(self):
        initial = self.store.count()
        self.store.upsert("user_count_test", [0.5] * 384, {"tag": "test"})
        self.assertEqual(self.store.count(), initial + 1)

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree("./test_chroma_db", ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
