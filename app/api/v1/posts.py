from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Tuple

from app.core.database import get_db
from app.models import sql_models as models
from app.models.sql_models import Post, Blog, User
from app.schemas import PostStatusResponse
from app.core.deps import get_current_user
from pydantic import BaseModel

from app.services.credit_service import calculate_required_credits
from app.services.gemini_service import generate_html
from app.services.image_service import WORKFLOW_PATH, generate_image_sync, save_image_bytes
import logging
import os
from pathlib import Path

LOGGER = logging.getLogger("posts")


def _workflow_path_for_runtime() -> str:
    """
    AS-IS: 상대경로 workflows/ai_marketing.json → 실행 위치에 따라 FileNotFound.
    TO-BE: image_service에서 resolve된 WORKFLOW_PATH를 우선 사용하되,
          사용자 요구사항(~/autoblog/backend/workflows/ai_marketing.json)도 존재하면 그쪽을 우선합니다.
    """
    try:
        p = Path(WORKFLOW_PATH)
        if p.exists():
            return str(p)
    except Exception:
        pass

    project_root = Path(__file__).resolve().parents[3]  # .../autoblog
    backend_candidate = project_root / "backend" / "workflows" / "ai_marketing.json"
    if backend_candidate.exists():
        return str(backend_candidate)

    return WORKFLOW_PATH

router = APIRouter()

# 블로그별 포스팅 현황을 묶어서 보여주기 위한 응답 구조
class BlogStatsResponse(BaseModel):
    blog_alias: str
    platform: str
    posts: List[PostStatusResponse]


class PostPreviewPayload(BaseModel):
    topic: str
    persona: str = "Friendly IT Expert"
    image_count: int = 3
    word_count_range: Tuple[int, int] = (800, 1200)
    img_prompts: list[str] | None = None
    custom_prompt: str | None = None
    free_trial: bool = False


async def process_image_generation(post_id: int, index: int, prompt: str):
    try:
        wf = _workflow_path_for_runtime()
        image_bytes = await generate_image_sync(wf, prompt)
        filename = f"post_{post_id}_image_{index}.png"
        url = save_image_bytes(filename, image_bytes)
        LOGGER.info("Image saved (static): %s", url)
    except Exception as exc:
        LOGGER.exception("Image generation failed (post=%s idx=%s type=%s): %s", post_id, index, type(exc).__name__, exc)



@router.get("/status", response_model=List[BlogStatsResponse])
def get_posting_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 내 모든 블로그와 그 안의 포스트들을 한 번에 가져옴 (Eager Loading)
    my_blogs = db.query(Blog).options(joinedload(Blog.posts))\
        .filter(Blog.owner_id == current_user.id).all()
    
    result = []
    for blog in my_blogs:
        # Pydantic 모델로 변환
        post_list = [PostStatusResponse.model_validate(p) for p in blog.posts]
        # 최신순 정렬
        post_list.sort(key=lambda x: x.created_at, reverse=True)
        
        result.append({
            "blog_alias": blog.alias or blog.blog_url,
            "platform": blog.platform_type,
            "posts": post_list
        })
        
    return result


@router.post("/preview")
async def generate_post_with_images(
    payload: PostPreviewPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.image_count < 1:
        raise HTTPException(status_code=400, detail="이미지 개수는 최소 1개 이상이어야 합니다.")

    blog = db.query(Blog).filter(Blog.owner_id == current_user.id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="등록된 블로그가 없어 미리보기를 생성할 수 없습니다.")

    new_post = Post(
        blog_id=blog.id,
        title=f"{payload.topic} #{payload.persona}",
        content="자동 생성된 초안입니다. 곧 Gemini가 업데이트합니다.",
        status="DRAFT",
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    credits_needed = calculate_required_credits(payload.image_count, payload.word_count_range)
    if not payload.free_trial:
        if current_user.current_credit < credits_needed:
            raise HTTPException(status_code=402, detail="크레딧이 부족합니다.")
        current_user.current_credit -= credits_needed
        credit_entry = models.CreditLog(
            user_id=current_user.id,
            amount=-credits_needed,
            action_type="PREVIEW_GEN",
            details={"topic": payload.topic, "images": payload.image_count},
        )
        db.add(credit_entry)

    final_prompt = payload.custom_prompt or f"Generate SEO-friendly HTML for {payload.topic} with persona {payload.persona}."
    html_result = await generate_html(payload.topic, payload.persona, final_prompt, payload.word_count_range, payload.image_count)
    new_post.content = html_result["html"]
    db.commit()

    image_urls: list[str] = []
    image_error: str | None = None
    img_prompts = payload.img_prompts or []
    for i in range(payload.image_count):
        prompt = img_prompts[i] if i < len(img_prompts) else f"{payload.topic} 이미지 프롬프트 #{i + 1}"
        try:
            wf = _workflow_path_for_runtime()
            image_bytes = await generate_image_sync(wf, prompt)
            filename = f"post_{new_post.id}_img_{i + 1}.png"
            url = save_image_bytes(filename, image_bytes)
            image_urls.append(url)
        except Exception as exc:
            # ComfyUI 미연결/네트워크 오류 등으로 이미지 생성이 실패해도 HTML은 제공해야 합니다.
            image_error = f"{type(exc).__name__}: {exc}"
            # 어떤 통신 에러인지 로그에 남김 (Connection/Timeout/FileNotFound 등)
            LOGGER.exception("Image generation failed; returning HTML only. (type=%s)", type(exc).__name__)
            break

    new_post.image_paths = image_urls
    db.commit()

    return {
        "status": "completed" if not image_error else "image_failed",
        "image_total": payload.image_count,
        "post_id": new_post.id,
        "html": html_result["html"],
        "summary": html_result.get("summary", ""),
        "credits_required": credits_needed,
        "images": image_urls,
        "image_error": image_error,
    }


@router.get("/keywords")
def get_keyword_tracking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    키워드 트래킹 테이블용 최소 엔드포인트.
    TODO: 실제 검색엔진 순위 수집/변동 로직 연동 전까지는 저장된 post.keyword_ranks 기반 또는 빈 배열을 반환합니다.
    """
    blogs = db.query(Blog).options(joinedload(Blog.posts)).filter(Blog.owner_id == current_user.id).all()
    rows: list[dict] = []
    for blog in blogs:
        for post in blog.posts:
            ranks = post.keyword_ranks or {}
            # ranks가 {"키워드": {"rank": 3, "change": 1, "updated_at": "...", "url": "..."}} 형태라고 가정
            for keyword, meta in ranks.items():
                if isinstance(meta, dict):
                    rows.append(
                        {
                            "keyword": keyword,
                            "platform": blog.platform_type,
                            "rank": meta.get("rank", 0),
                            "change": meta.get("change", 0),
                            "updated_at": meta.get("updated_at", ""),
                        }
                    )
    return rows

