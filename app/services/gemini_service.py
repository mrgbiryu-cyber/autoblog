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


async def analyze_blog(blog_url: str, alias: str | None, topic: str | None = None) -> dict:
    """
    Analyze the given blog URL using Gemini and return category + prompt recommendations.
    """
    description = alias or blog_url
    topic_context = f"\n현재 작성하려는 주제/키워드: {topic}" if topic else ""
    prompt = (
        "당신은 블로그 니치를 분석하는 전문가입니다.\n"
        "아래 URL/별칭과 주제를 분석해서 최적의 카테고리(한글)와 SEO 최적화 글 작성 지시 프롬프트(한글)를 JSON으로만 반환하세요.\n"
        "프롬프트에는 다음 SEO 규격 지침을 반드시 포함하세요:\n"
        "- '제목은 55자 이내로 작성하고, 메인 키워드를 가장 앞부분에 배치하세요.'\n"
        "- '본문 전체에 메인 키워드 1회, 서브 키워드 2회 이상 자연스럽게 포함하세요.'\n"
        "- '2줄 단위로 문단을 나누고 메타 설명을 120~160자로 작성하세요.'\n"
        f"제공된 주제({topic or '없음'})가 있는 경우, 해당 주제에 특화된 SEO 전략을 프롬프트에 녹여내세요.\n"
        "반드시 다음 형태만 허용됩니다: {\"category\": \"...\", \"prompt\": \"...\"}\n\n"
        f"URL/별칭: {description}{topic_context}"
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
    keywords: list[str] | None = None,
) -> dict:
    """
    압도적 SEO 최적화 엔진:
    - 제목: 30자 내외, 특수문자 배제, 검색 의도 중심
    - 키워드 분산: 메인 5-10회, 서브 3-5회 (연속 사용 금지)
    - 구조: 소제목 3-6개(질문형 포함), 리스트/표 활용, 2줄마다 줄바꿈
    - 이미지: 텍스트 삽입 금지, 이미지 하단 설명 문장 자동 생성
    """
    min_words, max_words = word_count_range
    prompt_text = prompt or f"{topic} 주제로 블로그 글을 작성하세요."
    
    main_keyword = keywords[0] if keywords and len(keywords) > 0 else topic
    sub_keywords = keywords[1:] if keywords and len(keywords) > 1 else []
    sub_kw_str = ", ".join(sub_keywords) if sub_keywords else "없음"

    full_prompt = (
        "당신은 검색 엔진 상위 노출을 보장하는 15년 경력의 SEO 전문 콘텐츠 디렉터입니다.\n"
        "다음 지침을 엄격히 준수하여 블로그 포스팅을 생성하고 JSON으로 반환하세요.\n\n"
        
        "[1. 핵심 SEO 전략 - 프롬프트 미노출 지침]\n"
        f"- 메인 키워드: '{main_keyword}' (본문 전체에 5~10회 골고루 분산, 연속 사용 절대 금지)\n"
        f"- 서브 키워드: '{sub_kw_str}' (각 3~5회 분산 배치)\n"
        "- 문체: AI가 쓴 느낌을 완벽히 배제하고, 동의어와 유사어를 활용하여 자연스럽게 작성하세요.\n"
        "- 일치성: 제목과 본문 내용이 100% 일치해야 하며 검색 의도를 정확히 관통해야 합니다.\n\n"
        
        "[2. 콘텐츠 구조 및 규격]\n"
        "- 제목: 30자 내외(검색 의도 포함, 특수문자 금지, 메인 키워드 전진 배치)\n"
        "- 메타 설명: 120~160자 (본문의 핵심을 요약하여 클릭을 유도)\n"
        "- 본문 구조: 소제목(h2, h3)을 3~6개 포함하고, 그중 최소 1개는 질문형 문장으로 작성하세요.\n"
        "- 가독성: 2줄마다 줄바꿈(<br> 또는 <p> 분리)을 적용하고 리스트(ul/ol), 표(table), 번호정리를 적극 활용하세요.\n"
        "- CTA: 본문 하단에 자연스러운 행동 유도 문구를 포함하세요.\n\n"
        
        "[3. 이미지 및 미디어 지침]\n"
        f"- 총 {image_count}개의 이미지 위치를 <!-- IMAGE_PLACEHOLDER_n --> 로 지정하세요.\n"
        "- **중요**: 각 이미지 위치 바로 아래에 해당 이미지를 설명하는 자연스러운 문장(이미지 캡션)을 1줄 추가하세요.\n"
        "- 이미지 프롬프트 생성 시 이미지 내에 어떠한 텍스트도 삽입하지 않도록 지시하세요.\n\n"
        
        "반드시 다음 JSON 형태로만 반환하세요:\n"
        "{\n"
        "  \"title\": \"SEO 최적화 제목\",\n"
        "  \"meta_description\": \"메타 설명\",\n"
        "  \"meta_keywords\": [\"키워드1\", \"키워드2\"],\n"
        "  \"body_html\": \"상세 HTML 본문\",\n"
        "  \"image_prompts\": [\"텍스트가 배제된 실사 스타일 프롬프트1\", ..., \"썸네일 프롬프트\"],\n"
        "  \"summary\": \"요약\"\n"
        "}\n\n"
        f"- 주제: {topic}\n"
        f"- 페르소나: {persona}\n"
        f"- 분량: {min_words}~{max_words}자\n"
        f"- 추가 지시: {prompt_text}\n"
    )

    raw = await _call_prompt(full_prompt)

    def sanitize_body(text: str) -> str:
        banned = ["SEO를 위한 한마디", "메타 설명 아이디어"]
        out_lines: list[str] = []
        for line in (text or "").splitlines():
            if any(b in line for b in banned):
                continue
            out_lines.append(line)
        return "\n".join(out_lines).strip()

    def build_html(title: str, meta_description: str, meta_keywords: list[str], body_html: str) -> str:
        kw = ", ".join([k.strip() for k in (meta_keywords or []) if str(k).strip()])
        body = sanitize_body(body_html)
        return (
            "<!doctype html>\n"
            "<html lang=\"ko\">\n"
            "<head>\n"
            "  <meta charset=\"utf-8\" />\n"
            f"  <title>{title}</title>\n"
            f"  <meta name=\"description\" content=\"{meta_description}\" />\n"
            f"  <meta name=\"keywords\" content=\"{kw}\" />\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
            "</head>\n"
            "<body>\n"
            f"{body}\n"
            "</body>\n"
            "</html>"
        )

    data = _try_parse_json_object(raw)
    if data:
        title = str(data.get("title") or topic).strip()
        # TO-BE: 제목 55자 제한 강제
        if len(title) > 55:
            # 키워드가 앞단에 배치되도록 자릅니다.
            title = title[:52].strip() + "..."
        
        meta_description = str(data.get("meta_description") or "").strip()
        # TO-BE: 메타 설명 120~160자 강제
        if len(meta_description) < 120:
            # 너무 짧으면 문장을 추가하거나 패딩
            meta_description = (meta_description + " " + title + "에 대한 상세한 정보를 확인해보세요.").strip()
            if len(meta_description) > 160:
                meta_description = meta_description[:157] + "..."
        elif len(meta_description) > 160:
            meta_description = meta_description[:157].strip() + "..."
        
        meta_keywords = data.get("meta_keywords") or []
        if not isinstance(meta_keywords, list):
            meta_keywords = [str(meta_keywords)]
        
        summary = str(data.get("summary") or "").strip()
        body_html = str(data.get("body_html") or "").strip()
        cta_text = str(data.get("cta_text") or "더 알아보기").strip()
        
        # TO-BE: CTA 버튼 자동 삽입
        if "<div class='cta-button'>" not in body_html and "<div class=\"cta-button\">" not in body_html:
            cta_html = f"""\n<div class="cta-button" style="text-align: center; margin-top: 40px;">
  <a href="#" style="display: inline-block; padding: 15px 30px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">{cta_text}</a>
</div>"""
            body_html = body_html + cta_html
        
        image_prompts = data.get("image_prompts") or []
        if not isinstance(image_prompts, list):
            image_prompts = []
        
        # TO-BE: 마지막 프롬프트를 썸네일 전용으로 강제 보정 (Reviewer 단계에서도 하지만 생성 시점 최적화)
        if image_prompts:
            last_idx = len(image_prompts) - 1
            if "thumbnail" not in image_prompts[last_idx].lower() and "대표 이미지" not in image_prompts[last_idx].lower():
                image_prompts[last_idx] = f"{topic} 주제의 블로그 썸네일용 대표 이미지, 클릭을 유도하는 매력적인 디자인, 고해상도, 리얼리스틱"
        
        html = build_html(title, meta_description, meta_keywords, body_html)
        return {
            "html": html,
            "summary": summary,
            "title": title,
            "image_prompts": image_prompts,
            "cta_text": cta_text,
            "seo_title_length": len(title),
            "meta_description_length": len(meta_description)
        }

    try:
        data2 = json.loads(raw.strip())
        if isinstance(data2, dict):
            title = str(data2.get("title") or topic).strip()
            meta_description = str(data2.get("meta_description") or "").strip()
            meta_keywords = data2.get("meta_keywords") or []
            if not isinstance(meta_keywords, list):
                meta_keywords = [str(meta_keywords)]
            summary = str(data2.get("summary") or "").strip()
            body_html = str(data2.get("body_html") or "").strip()
            image_prompts = data2.get("image_prompts") or []
            if not isinstance(image_prompts, list):
                image_prompts = []
            html = build_html(title, meta_description, meta_keywords, body_html)
            return {"html": html, "summary": summary, "title": title, "image_prompts": image_prompts}
    except Exception:
        pass

    LOGGER.warning("Gemini HTML response not JSON; returning raw text.")
    return {"html": raw, "summary": raw[:120], "title": topic, "image_prompts": []}

