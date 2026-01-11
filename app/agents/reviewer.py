import re
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


DEFAULT_BANNED_SYSTEM_PHRASES = [
    "SEO를 위한 한마디",
    "메타 설명 아이디어",
]

DEFAULT_BANNED_IMAGE_TERMS = [
    # 주제와 무관하게 마케팅/대시보드 이미지를 유도하는 단어들
    "marketing",
    "dashboard",
    "automation",
    "saas",
    "landing page",
    "ui",
    "ux",
]


def _tokenize(text: str) -> List[str]:
    t = (text or "").strip()
    if not t:
        return []
    # 간단 토큰화: 영문/숫자/한글 단위로 분리
    tokens = re.findall(r"[A-Za-z0-9가-힣]+", t)
    # 너무 짧은 토큰은 제거
    return [x for x in tokens if len(x) >= 2]


def _contains_any(text: str, phrases: List[str]) -> bool:
    lower = (text or "").lower()
    for p in phrases:
        if p.lower() in lower:
            return True
    return False


def filter_system_phrases(text: str, banned_phrases: List[str] | None = None) -> Tuple[str, List[str]]:
    """
    Writer 산출물에서 독자에게 노출되면 안 되는 시스템/기획 문구를 제거합니다.
    """
    banned_phrases = banned_phrases or DEFAULT_BANNED_SYSTEM_PHRASES
    found: List[str] = []
    out_lines: List[str] = []
    for line in (text or "").splitlines():
        if any(p in line for p in banned_phrases):
            for p in banned_phrases:
                if p in line and p not in found:
                    found.append(p)
            continue
        out_lines.append(line)
    return "\n".join(out_lines).strip(), found


def validate_and_fix_image_prompts(
    topic: str,
    image_prompts: List[str],
    banned_terms: List[str] | None = None,
) -> Tuple[List[str], List[str]]:
    """
    이미지 프롬프트가 본문 주제와 정합적인지 검사하고,
    불일치하면 topic을 강제 포함시키는 형태로 자동 보정합니다.
    """
    banned_terms = banned_terms or DEFAULT_BANNED_IMAGE_TERMS
    topic_tokens = _tokenize(topic)
    issues: List[str] = []
    fixed: List[str] = []

    for idx, p in enumerate(image_prompts or []):
        prompt = (p or "").strip()
        if not prompt:
            prompt = f"{topic} 사진, 자연광, 고해상도, 리얼리스틱"
            issues.append(f"image_prompts[{idx}] empty -> default topic prompt")
            fixed.append(prompt)
            continue

        lower = prompt.lower()
        has_topic = topic.strip() and topic.strip().lower() in lower
        if not has_topic:
            for tok in topic_tokens:
                if tok.lower() in lower:
                    has_topic = True
                    break

        if not has_topic:
            # 마케팅/대시보드 성향 단어가 있으면 제거하고 주제로 고정
            cleaned = prompt
            if _contains_any(cleaned, banned_terms):
                for term in banned_terms:
                    cleaned = re.sub(re.escape(term), "", cleaned, flags=re.IGNORECASE).strip()
                issues.append(f"image_prompts[{idx}] contains banned marketing terms -> sanitized")
            issues.append(f"image_prompts[{idx}] topic mismatch -> forced topic prefix")
            prompt = f"{topic}, {cleaned}".strip().strip(",")

        fixed.append(prompt)

    return fixed, issues


def sanitize_final_html(html: str) -> Tuple[str, List[str]]:
    """
    최종 산출물 정제:
    - 금칙 문구 제거
    - <script> 제거
    - 광고/기획 텍스트 등 불필요 요소 제거(보수적)
    """
    cleaned = html or ""
    issues: List[str] = []

    # script 제거
    script_re = re.compile(r"<script\b[^>]*>[\s\S]*?</script>", re.IGNORECASE)
    if script_re.search(cleaned):
        cleaned = script_re.sub("", cleaned)
        issues.append("removed <script> blocks")

    # 금칙 문구 제거(HTML 전체 기준)
    for p in DEFAULT_BANNED_SYSTEM_PHRASES:
        if p in cleaned:
            cleaned = cleaned.replace(p, "")
            issues.append(f"removed banned phrase: {p}")

    # adsense div 제거(있으면)
    ads_re = re.compile(r"<div[^>]*class=\"adsense\"[^>]*>[\s\S]*?</div>", re.IGNORECASE)
    if ads_re.search(cleaned):
        cleaned = ads_re.sub("", cleaned)
        issues.append("removed adsense blocks")

    return cleaned.strip(), issues


@dataclass
class ReviewResult:
    ok: bool
    feedback: str
    issues: List[str]
    cleaned_content: str | None = None
    cleaned_image_prompts: List[str] | None = None
    cleaned_html: str | None = None


class ReviewerAgent:
    """
    Reviewer Agent:
    - 텍스트에서 시스템 메시지 제거/재작성 요구
    - 이미지 프롬프트 주제 정합성 검증
    - 최종 HTML 정제
    """

    def review_writer_output(self, draft: Dict[str, Any], topic: str) -> ReviewResult:
        content = draft.get("content", "")
        image_prompts = draft.get("image_prompts", []) or []
        cleaned_content, found = filter_system_phrases(content)
        cleaned_prompts, prompt_issues = validate_and_fix_image_prompts(topic, list(image_prompts))

        issues = []
        if found:
            issues.append(f"removed system phrases: {', '.join(found)}")
        issues.extend(prompt_issues)

        ok = len(found) == 0 and len(prompt_issues) == 0
        feedback_parts = []
        if found:
            feedback_parts.append("본문에 기획/시스템 문구가 포함되었습니다. 해당 문구를 제거하고 자연스러운 문장으로만 작성해주세요.")
        if prompt_issues:
            feedback_parts.append("이미지 프롬프트가 주제와 불일치합니다. 모든 이미지 프롬프트에 주제 키워드를 포함해주세요.")

        return ReviewResult(
            ok=ok,
            feedback=" ".join(feedback_parts).strip() or "OK",
            issues=issues,
            cleaned_content=cleaned_content,
            cleaned_image_prompts=cleaned_prompts,
        )

    def review_final_html(self, html: str) -> ReviewResult:
        cleaned, issues = sanitize_final_html(html)
        ok = len(issues) == 0
        feedback = "OK" if ok else "최종 HTML에서 불필요 요소/금칙 문구를 제거했습니다."
        return ReviewResult(ok=ok, feedback=feedback, issues=issues, cleaned_html=cleaned)


