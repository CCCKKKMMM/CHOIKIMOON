"""
TDD: TMDB 검색 개선 테스트
- 에피소드 번호 제거 후 시리즈명으로 검색
"""

import unittest
from tmdb import clean_title, search_tv, search_movie


class TestCleanTitle(unittest.TestCase):
    """에피소드 번호 제거 함수 테스트"""

    def test_removes_korean_episode_number(self):
        self.assertEqual(clean_title("태양의 후예 01회"), "태양의 후예")
        self.assertEqual(clean_title("미스터 션샤인 12화"), "미스터 션샤인")

    def test_removes_episode_with_dot(self):
        self.assertEqual(clean_title("S.W.A.T 3 03회."), "S.W.A.T 3")
        self.assertEqual(clean_title("S.W.A.T 4 01ȸ."), "S.W.A.T 4")

    def test_removes_zero_padded_episode(self):
        self.assertEqual(clean_title("1997 이수일과심순애 01회"), "1997 이수일과심순애")
        self.assertEqual(clean_title("MBC 베스트극장 27회"), "MBC 베스트극장")

    def test_removes_season_episode(self):
        self.assertEqual(clean_title("스타워즈 S01E01"), "스타워즈")
        self.assertEqual(clean_title("프렌즈 시즌1 1화"), "프렌즈")

    def test_no_change_for_movie(self):
        self.assertEqual(clean_title("기생충"), "기생충")
        self.assertEqual(clean_title("어벤져스: 엔드게임"), "어벤져스: 엔드게임")

    def test_removes_trailing_whitespace(self):
        result = clean_title("태양의 후예 01회  ")
        self.assertEqual(result, "태양의 후예")

    def test_removes_episode_with_year(self):
        self.assertEqual(clean_title("나는 자연인이다 2014 01회."), "나는 자연인이다 2014")

    def test_removes_ep_prefix(self):
        self.assertEqual(clean_title("어게인 마이 라이프 EP01"), "어게인 마이 라이프")


class TestSearchTvWithCleanTitle(unittest.TestCase):
    """에피소드 번호 제거 후 TMDB 검색 테스트"""

    def test_search_tv_with_episode_title_returns_result(self):
        """에피소드 번호가 포함된 제목으로도 감독 정보를 찾아야 함"""
        result = search_tv("태양의 후예 01회")
        # 에피소드 번호 제거 후 검색하므로 결과가 있어야 함
        self.assertIsInstance(result, dict)

    def test_search_tv_cleans_before_search(self):
        """검색 전 제목 정제 적용 확인"""
        result_raw = search_tv("파친코 1화")
        result_clean = search_tv("파친코")
        # 둘 다 같은 결과여야 함 (내부적으로 clean_title 적용)
        self.assertEqual(result_raw.get("director"), result_clean.get("director"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
