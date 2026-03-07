import json
import time
import anthropic
from config import ANTHROPIC_API_KEY, MODEL, REQUEST_DELAY, MAX_RETRIES

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _call_claude(prompt: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            time.sleep(REQUEST_DELAY)
            return response.content[0].text.strip()
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"  [Rate Limit] {wait}초 대기 후 재시도...")
            time.sleep(wait)
        except anthropic.APIError as e:
            print(f"  [API Error] {e} (시도 {attempt+1}/{MAX_RETRIES})")
            time.sleep(5)
    return ""


def _parse_json(text: str) -> dict:
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except json.JSONDecodeError:
        pass
    return {}


# ── smry 채우기 ──────────────────────────────────────────────────────
def fetch_smry(asset_nm: str, ct_cl: str, genre: str, director: str) -> str:
    prompt = f"""다음 영상 콘텐츠의 줄거리(시놉시스)를 한국어 2~4문장으로 작성해주세요.
반드시 JSON 형식으로만 응답하세요.

콘텐츠 정보:
- 제목: {asset_nm}
- 유형: {ct_cl}
- 장르: {genre or '알 수 없음'}
- 감독: {director or '알 수 없음'}

응답 형식:
{{"smry": "줄거리 내용", "confidence": "high/medium/low"}}

정보가 전혀 없어 작성 불가능한 경우:
{{"smry": null, "confidence": "none"}}"""

    result = _parse_json(_call_claude(prompt))
    smry = result.get("smry")
    confidence = result.get("confidence", "low")
    if smry and confidence != "none":
        return smry
    return ""


# ── director 채우기 ──────────────────────────────────────────────────
def fetch_director(asset_nm: str, ct_cl: str, genre: str, series_nm: str) -> str:
    prompt = f"""다음 영상 콘텐츠의 감독/연출자 이름을 알려주세요.
반드시 JSON 형식으로만 응답하세요.

콘텐츠 정보:
- 제목: {asset_nm}
- 유형: {ct_cl}
- 장르: {genre or '알 수 없음'}
- 시리즈명: {series_nm or '알 수 없음'}

응답 형식:
{{"director": "감독명", "confidence": "high/medium/low"}}

확실하지 않거나 알 수 없는 경우:
{{"director": null, "confidence": "none"}}"""

    result = _parse_json(_call_claude(prompt))
    director = result.get("director")
    confidence = result.get("confidence", "low")
    if director and confidence in ("high", "medium"):
        return director
    return ""


# ── series_nm 채우기 ─────────────────────────────────────────────────
def fetch_series_nm(asset_nm: str, ct_cl: str, genre: str) -> str:
    prompt = f"""다음 에피소드/회차 콘텐츠가 속하는 시리즈명을 알려주세요.
에피소드 번호나 회차를 제거한 순수 시리즈 제목만 응답하세요.
반드시 JSON 형식으로만 응답하세요.

콘텐츠 정보:
- 제목: {asset_nm}
- 유형: {ct_cl}
- 장르: {genre or '알 수 없음'}

응답 형식:
{{"series_nm": "시리즈명", "confidence": "high/medium/low"}}

단편/독립작이거나 알 수 없는 경우:
{{"series_nm": null, "confidence": "none"}}"""

    result = _parse_json(_call_claude(prompt))
    series_nm = result.get("series_nm")
    confidence = result.get("confidence", "low")
    if series_nm and confidence in ("high", "medium"):
        return series_nm
    return ""
