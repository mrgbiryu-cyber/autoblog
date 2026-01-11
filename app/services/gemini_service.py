"""
Gemini integration helpers.

현재 운영 환경(GCP)에서 설치되는 신규 SDK는 `google-genai`이며,
사용법은 `from google import genai; client = genai.Client(api_key=...)` 입니다.
기존 `google.generativeai`는 deprecated 되었고, `google.genai.configure(...)`는 존재하지 않아
백엔드가 import 단계에서 크래시가 나므로 절대 호출하면 안 됩니다.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

LOGGER = logging.getLogger("gemini_service")

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
GENAI_MODEL = os.getenv("GENAI_MODEL_NAME", "gemini-2.5-flash")

_client: Any | None = None
_legacy_genai: Any | None = None

# 1) 신규 SDK 우선 (google-genai)
try:
    from google import genai as _google_genai  # type: ignore

    if GENAI_API_KEY:
        _client = _google_genai.Client(api_key=GENAI_API_KEY)
    else:
        LOGGER.warning("GENAI_API_KEY not configured; Gemini calls will fail.")
except Exception as exc:
    LOGGER.warning("google-genai import/init failed: %s", exc)

# 2) 레거시 SDK fallback (google-generativeai) - 설치되어 있으면 사용
if _client is None:
    try:
        import google.generativeai as _legacy_genai  # type: ignore

        if GENAI_API_KEY:
            _legacy_genai.configure(api_key=GENAI_API_KEY)
        else:
            LOGGER.warning("GENAI_API_KEY not configured; Gemini calls will fail.")
    except Exception as exc:
        LOGGER.warning("google-generativeai import/init failed: %s", exc)
        _legacy_genai = None


def _require_gemini() -> None:
    if _client is None and _legacy_genai is None:
        raise RuntimeError("Gemini SDK가 초기화되지 않았습니다. (GENAI_API_KEY 또는 SDK 설치 상태 확인 필요)")


def _extract_text(resp: Any) -> str:
    # google-genai: response.text 가 일반적
    text = getattr(resp, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    # legacy: response.text 가 있을 수도 있음
    text = getattr(resp, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()

    return str(resp)


def _try_parse_json_object(raw: str) -> dict | None:
    """
    Gemini가 다음과 같은 형태로 응답하는 경우를 최대한 복구합니다.
    - ```json ... ``` 코드펜스 포함
    - 앞/뒤 설명 텍스트가 붙어 있음
    - JSON 오브젝트가 문자열로 반환됨
    """
    if not raw:
        return None

    text = raw.strip()

    # 코드펜스 제거
    if text.startswith("```"):
        # ```json\n{...}\n``` 또는 ```\n{...}\n```
        parts = text.split("```")
        # parts: ["", "json\n{...}\n", ""]
        if len(parts) >= 2:
            text = parts[1].strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()

    # 첫 JSON object로 보이는 구간만 추출
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = text[start : end + 1].strip()
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


async def _call_prompt(prompt: str) -> str:
    _require_gemini()

    def sync_call() -> str:
        if _client is not None:
            resp = _client.models.generate_content(model=GENAI_MODEL, contents=prompt)
            return _extract_text(resp)

        # legacy fallback
        model = _legacy_genai.GenerativeModel(GENAI_MODEL)  # type: ignore[union-attr]
        resp = model.generate_content(prompt)
        return _extract_text(resp)

    return await asyncio.to_thread(sync_call)


async def analyze_blog(blog_url: str, alias: str | None) -> dict:
    """
    Analyze the given blog URL using Gemini and return category + prompt recommendations.
    """
    description = alias or blog_url
    prompt = (
        "당신은 블로그 니치를 분석하는 전문가입니다.\n"
        "아래 URL/별칭을 분석해서 최적의 카테고리(한글)와 SEO 최적화 글 작성 지시 프롬프트(한글)를 JSON으로만 반환하세요.\n"
        "반드시 다음 형태만 허용됩니다: {\"category\": \"...\", \"prompt\": \"...\"}\n\n"
        f"URL/별칭: {description}"
    )

    raw = await _call_prompt(prompt)

    data = _try_parse_json_object(raw)
    if data:
        return {
            "category": str(data.get("category") or description).strip(),
            "prompt": str(data.get("prompt") or f"{description}에 맞는 SEO 글을 작성하세요.").strip(),
        }

    # 그래도 실패하면 raw가 JSON 문자열일 수도 있으니 한 번 더 시도
    try:
        data2 = json.loads(raw.strip())
        if isinstance(data2, dict):
            return {
                "category": str(data2.get("category") or description).strip(),
                "prompt": str(data2.get("prompt") or f"{description}에 맞는 SEO 글을 작성하세요.").strip(),
            }
    except Exception:
        pass

    LOGGER.warning("Gemini analyze response not JSON; using fallback.")
    return {"category": description, "prompt": raw.strip()}


async def generate_html(
    topic: str,
    persona: str,
    prompt: str | None,
    word_count_range: tuple[int, int],
    image_count: int,
) -> dict:
    """
    Generate SEO-optimized HTML snippet based on topic, persona, and custom prompt.
    """
    min_words, max_words = word_count_range
    prompt_text = prompt or f"{topic} 주제로 SEO 최적화 HTML을 작성하세요."

    full_prompt = (
        "당신은 SEO 전문 콘텐츠 에디터입니다.\n"
        "다음 입력을 바탕으로 블로그 포스팅을 HTML로 작성하고, JSON으로만 반환하세요.\n"
        "반드시 다음 형태만 허용됩니다: {\"html\": \"...\", \"summary\": \"...\"}\n\n"
        f"- 주제: {topic}\n"
        f"- 페르소나: {persona}\n"
        f"- 글자수: {min_words}~{max_words}\n"
        f"- 이미지 개수: {image_count}\n"
        f"- 작성 지시: {prompt_text}\n\n"
        "HTML에는 제목(h1), 소제목(h2/h3), 본문(p), 목록(ul/ol)을 적절히 포함하고,\n"
        "이미지 위치는 <!-- IMAGE_PLACEHOLDER --> 로 표시하세요.\n"
    )

    raw = await _call_prompt(full_prompt)

    data = _try_parse_json_object(raw)
    if data:
        return {"html": str(data.get("html") or raw), "summary": str(data.get("summary") or "")}

    try:
        data2 = json.loads(raw.strip())
        if isinstance(data2, dict):
            return {"html": str(data2.get("html") or raw), "summary": str(data2.get("summary") or "")}
    except Exception:
        pass

    LOGGER.warning("Gemini HTML response not JSON; returning raw text.")
    return {"html": raw, "summary": raw[:120]}

