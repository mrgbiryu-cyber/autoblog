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
from app.services.image_service import generate_image_sync
import logging
import os

LOGGER = logging.getLogger("posts")
WORKFLOW_PATH = os.getenv("COMFYUI_WORKFLOW_PATH", "workflows/ai_marketing.json")

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


async def process_image_generation(post_id: int, index: int, prompt: str):
    try:
        image_bytes = await generate_image_sync(WORKFLOW_PATH, prompt)
        os.makedirs("generated_images", exist_ok=True)
        file_path = os.path.join("generated_images", f"post_{post_id}_image_{index}.png")
        with open(file_path, "wb") as fp:
            fp.write(image_bytes)
        LOGGER.info("Image saved: %s", file_path)
    except Exception as exc:
        LOGGER.error("Failed to generate image #%s for post %s: %s", index, post_id, exc)



@router.get("/status", response_model=List[BlogStatsResponse])
def get_posting_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 내 모든 블로그와 그 안의 포스트들을 한 번에 가져옴 (Eager Loading)
    my_blogs = db.query(Blog).options(joinedload(Blog.posts))\
        .filter(Blog.user_id == current_user.id).all()
    
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

    blog = db.query(Blog).filter(Blog.user_id == current_user.id).first()
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

    image_files = []
    img_prompts = payload.img_prompts or []
    for i in range(payload.image_count):
        prompt = img_prompts[i] if i < len(img_prompts) else f"{payload.topic} 이미지 프롬프트 #{i + 1}"
        image_bytes = await generate_image_sync(WORKFLOW_PATH, prompt)
        os.makedirs("generated_images", exist_ok=True)
        filename = f"post_{new_post.id}_img_{i + 1}.png"
        path = os.path.join("generated_images", filename)
        with open(path, "wb") as fp:
            fp.write(image_bytes)
        image_files.append(path)

    return {
        "status": "completed",
        "image_total": payload.image_count,
        "post_id": new_post.id,
        "html": html_result["html"],
        "summary": html_result.get("summary", ""),
        "credits_required": credits_needed,
        "images": image_files,
    }

