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
    keywords: list[str] | None = None,  # TO-BE: 키워드 리스트 추가
) -> dict:
    """
    Generate SEO-optimized HTML document + metadata + image prompts.

    TO-BE 요구사항:
    - 제목: 55자 이내, 키워드 전진 배치
    - 메타 설명: 120~160자
    - 본문: 2줄 단위 문단 나누기 (모바일 최적화)
    - CTA 버튼: 본문 하단 자동 삽입
    - 썸네일: 마지막 이미지 프롬프트를 썸네일 전용으로 생성
    - 이미지 프롬프트: 주제 키워드 포함 필수 (정합성 100%)
    """
    min_words, max_words = word_count_range
    prompt_text = prompt or f"{topic} 주제로 SEO 최적화 HTML을 작성하세요."
    keyword_str = ", ".join(keywords or [])

    full_prompt = (
        "당신은 SEO 전문 콘텐츠 에디터입니다.\n"
        "다음 입력을 바탕으로 블로그 포스팅을 생성하되, 결과는 JSON으로만 반환하세요.\n\n"
        "[SEO 규격 - 필수 준수]\n"
        f"- 제목: 55자 이내, 메인 키워드({keyword_str})를 가능한 문장 맨 앞에 배치\n"
        "- 메타 설명: 120~160자 (정확히 이 범위 내)\n"
        f"- 본문: 메인 키워드 1회, 서브 키워드 2회 이상 포함 (자연스러운 맥락 유지)\n"
        "- 문단: 2줄 단위 문단 나누기 (모바일 최적화, <p> 태그 2~3문장 단위)\n"
        "- CTA: 본문 하단에 행동 유도 버튼 포함 (<div class='cta-button'>)\n\n"
        "[이미지 프롬프트 규격]\n"
        f"- 총 {image_count}개 생성\n"
        f"- 마지막 이미지는 썸네일 전용 (대표 이미지, 클릭 유도, 고해상도)\n"
        "- 모든 이미지는 '다이어그램', '플로우차트', '마케팅 인포그래픽' 형태를 절대 피하고, 본문 내용이 실제로 일어나는 '실사 장면'이나 '구체적인 정물/현장'으로 묘사하세요.\n"
        f"- 본문에서 다루는 구체적인 소재(예: 부동산이면 건물/계약/지도, 재테크면 금리/현금/그래프 등)를 중심으로 시각적 장면을 만드세요.\n\n"
        "[중요 금지사항]\n"
        "- 본문(body_html)에 기획 단계 문구(예: 'SEO를 위한 한마디', '메타 설명 아이디어') 절대 포함 금지\n"
        "- 메타 설명/키워드/제목은 meta_description/meta_keywords/title 필드로만 제공\n\n"
        "반드시 다음 형태만 허용됩니다(코드펜스 금지):\n"
        "{\n"
        "  \"title\": \"키워드 포함 55자 이내 제목\",\n"
        "  \"meta_description\": \"120~160자 메타 설명\",\n"
        "  \"meta_keywords\": [\"키워드1\", \"키워드2\"],\n"
        "  \"summary\": \"요약\",\n"
        "  \"body_html\": \"2줄 단위 문단 HTML + CTA 버튼\",\n"
        "  \"image_prompts\": [\"프롬프트1\", ..., \"썸네일 전용 프롬프트\"],\n"
        "  \"cta_text\": \"CTA 버튼 문구\"\n"
        "}\n\n"
        f"- 주제: {topic}\n"
        f"- 페르소나: {persona}\n"
        f"- 글자수: {min_words}~{max_words}\n"
        f"- 키워드: {keyword_str}\n"
        f"- 이미지 개수: {image_count}\n"
        f"- 작성 지시: {prompt_text}\n\n"
        "body_html에는 제목(h1), 소제목(h2/h3), 본문(p), 목록(ul/ol)을 적절히 포함하고,\n"
        f"이미지 위치는 <!-- IMAGE_PLACEHOLDER_1 --> 부터 <!-- IMAGE_PLACEHOLDER_{image_count} --> 까지 순서대로 포함하세요.\n"
        f"image_prompts는 반드시 {image_count}개를 생성하되, 주제어({topic})에 얽매이지 말고 **작성한 본문의 각 문단이 설명하는 실제 장면**을 사진가가 촬영한 것처럼 구체적으로 묘사하세요.\n"
        "마지막 이미지는 '글 전체의 핵심 주제를 상징하는 고해상도 대표 이미지'로 작성하세요.\n"
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

