"""
TMDB API 클라이언트 - VOD 메타데이터 조회 (1차 소스)

환경변수 설정:
  export TMDB_API_KEY="your_api_key_here"
  TMDB API 키 발급: https://www.themoviedb.org/settings/api
"""

import re
import time
import requests
from config import TMDB_API_KEY, TMDB_BASE_URL, TMDB_LANGUAGE, REQUEST_DELAY

# 에피소드 번호 패턴: "01회", "12화", "EP01", "S01E01", "시즌1 1화" 등
_EPISODE_PATTERN = re.compile(
    r'\s*(?:'
    r'S\d{1,2}E\d{1,2}'           # S01E01
    r'|시즌\s*\d+\s*\d*화?'        # 시즌1, 시즌1 1화
    r'|EP\s*\d+'                   # EP01
    r'|\d{1,3}\s*[화회ȸ]\.?'      # 01화, 12회, 01ȸ.
    r')\s*$',
    re.IGNORECASE
)


def clean_title(title: str) -> str:
    """제목에서 에피소드 번호를 제거하여 시리즈명 반환"""
    return _EPISODE_PATTERN.sub("", title).strip()


def _get(endpoint: str, params: dict = None) -> dict:
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    params["language"] = TMDB_LANGUAGE
    try:
        resp = requests.get(f"{TMDB_BASE_URL}{endpoint}", params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("  [TMDB] API 키 오류 - TMDB_API_KEY 환경변수를 확인하세요")
        return {}
    except Exception:
        return {}


def search_movie(title: str) -> dict:
    """영화 검색 → {smry, director}"""
    if not TMDB_API_KEY:
        return {}

    data = _get("/search/movie", {"query": clean_title(title)})
    results = data.get("results", [])
    if not results:
        return {}

    movie = results[0]
    movie_id = movie["id"]
    smry = movie.get("overview", "")

    # 감독 조회
    credits = _get(f"/movie/{movie_id}/credits")
    director = ""
    for crew in credits.get("crew", []):
        if crew.get("job") == "Director":
            director = crew.get("name", "")
            break

    time.sleep(REQUEST_DELAY)
    return {
        "smry": smry,
        "director": director,
    }


def search_tv(title: str) -> dict:
    """TV/드라마 검색 → {smry, director, series_nm}"""
    if not TMDB_API_KEY:
        return {}

    data = _get("/search/tv", {"query": clean_title(title)})
    results = data.get("results", [])
    if not results:
        return {}

    show = results[0]
    show_id = show["id"]
    smry = show.get("overview", "")
    series_nm = show.get("name", "")

    # 감독/연출자: created_by 우선, 없으면 credits crew
    details = _get(f"/tv/{show_id}")
    created_by = details.get("created_by", [])
    director = created_by[0]["name"] if created_by else ""

    if not director:
        credits = _get(f"/tv/{show_id}/credits")
        for crew in credits.get("crew", []):
            if crew.get("job") in ("Director", "Series Director"):
                director = crew.get("name", "")
                break

    time.sleep(REQUEST_DELAY)
    return {
        "smry": smry,
        "director": director,
        "series_nm": series_nm,
    }
