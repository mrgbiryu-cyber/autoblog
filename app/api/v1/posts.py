from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Tuple
from datetime import datetime

from app.core.database import get_db
from app.models import sql_models as models
from app.models.sql_models import Post, Blog, User
from app.schemas import PostStatusResponse
from app.core.deps import get_current_user
from pydantic import BaseModel

from app.services.credit_service import calculate_required_credits
from app.services.gemini_service import generate_html
from app.services.image_service import WORKFLOW_PATH, generate_image_sync, save_image_bytes
from app.services.tracking_service import tracking_service
from app.services.publisher_api import publish_post
from app.agents.reviewer import sanitize_final_html, validate_and_fix_image_prompts
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

from sqlalchemy import and_, or_
from datetime import timedelta

# ... existing imports ...

@router.delete("/cleanup")
def cleanup_old_posts(db: Session = Depends(get_db)):
    """
    7일이 지난 임시저장(DRAFT) 포스트와 관련 이미지를 삭제합니다.
    """
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # 7일 이상 된 DRAFT 포스트 조회
    old_posts = db.query(Post).filter(
        and_(
            Post.status == "DRAFT",
            Post.created_at < seven_days_ago
        )
    ).all()
    
    count = 0
    for post in old_posts:
        # 이미지 파일 삭제
        if post.image_paths:
            for path in post.image_paths:
                try:
                    full_path = Path(__file__).resolve().parents[3] / "static" / path.lstrip("/")
                    if full_path.exists():
                        os.remove(full_path)
                except Exception as e:
                    LOGGER.error(f"Failed to delete image {path}: {e}")
        
        db.delete(post)
        count += 1
    
    db.commit()
    return {"status": "ok", "deleted_count": count}


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
    keywords: list[str] | None = None # TO-BE: 키워드 리스트 추가


async def process_image_generation(post_id: int, index: int, prompt: str, filename: str):
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        wf = _workflow_path_for_runtime()
        # SDXL 프롬프트에 텍스트 배제 지시어 추가
        final_prompt = f"{prompt}, no text, no letters, high quality photography"
        image_bytes = await generate_image_sync(wf, final_prompt)
        url = save_image_bytes(filename, image_bytes)

        # [SEO 로그] 저장된 파일명과 주제 연동 확인
        LOGGER.info(f"SEO Image Saved: {filename} for post {post_id}")

        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            paths = post.image_paths or []
            if url not in paths:
                paths.append(url)
                post.image_paths = paths
                # 모든 이미지가 생성되었는지 확인
                if len(paths) >= post.expected_image_count:
                    post.img_gen_status = "COMPLETED"
                else:
                    post.img_gen_status = "PROCESSING"
                db.commit()
    except Exception as exc:
        LOGGER.exception("Image generation failed (post=%s idx=%s): %s", post_id, index, exc)
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            if "timeout" in str(exc).lower():
                post.img_gen_status = "TIMEOUT"
            else:
                post.img_gen_status = "FAILED"
            db.commit()
    finally:
        db.close()



from fastapi.responses import FileResponse, StreamingResponse
import io

@router.get("/{post_id}/download/html")
async def download_post_html(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = db.query(Post).join(Blog).filter(Post.id == post_id, Blog.owner_id == current_user.id).first()
    if not post or not post.content:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다.")
    
    filename = f"post_{post_id}.html"
    return StreamingResponse(
        io.BytesIO(post.content.encode("utf-8")),
        media_type="text/html",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{post_id}/download/images")
async def download_post_images(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    import zipfile
    post = db.query(Post).join(Blog).filter(Post.id == post_id, Blog.owner_id == current_user.id).first()
    if not post or not post.image_paths:
        raise HTTPException(status_code=404, detail="이미지가 없습니다.")
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for path in post.image_paths:
            try:
                # static/generated_images/...
                full_path = Path(__file__).resolve().parents[3] / "static" / path.lstrip("/")
                if full_path.exists():
                    zip_file.write(full_path, arcname=os.path.basename(path))
            except Exception as e:
                LOGGER.error(f"Failed to add image {path} to zip: {e}")
    
    zip_buffer.seek(0)
    filename = f"post_{post_id}_images.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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
    background_tasks: BackgroundTasks,
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
        expected_image_count=payload.image_count,
        img_gen_status="PROCESSING"
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
    html_result = await generate_html(
        payload.topic, 
        payload.persona, 
        final_prompt, 
        payload.word_count_range, 
        payload.image_count,
        keywords=payload.keywords
    )
    # Reviewer 최종 정제 (금칙 문구/스크립트 제거 등)
    cleaned_html, _issues = sanitize_final_html(html_result["html"])
    html_result["html"] = cleaned_html
    new_post.content = cleaned_html
    if html_result.get("title"):
        new_post.title = str(html_result["title"])
    db.commit()

    # TO-BE: 이미지 생성은 백그라운드로 돌리고, HTML은 즉시 반환해 Nginx 504를 방지합니다.
    # 이미지 프롬프트 우선순위:
    # 1) 요청 payload.img_prompts (직접 지정)
    # 2) Gemini가 반환한 image_prompts (주제 연동)
    # 3) topic 기반 기본값
    img_prompts = payload.img_prompts or html_result.get("image_prompts") or []
    if not isinstance(img_prompts, list):
        img_prompts = []
    img_prompts, _img_issues = validate_and_fix_image_prompts(payload.topic, img_prompts)

    # [SEO 고도화] 파일명에 키워드 주입 및 랜덤 세션 키 결합
    import uuid
    import re
    
    main_kw = payload.keywords[0] if payload.keywords else payload.topic
    sub_kw = payload.keywords[1] if payload.keywords and len(payload.keywords) > 1 else "seo"
    # 파일명 사용 가능하게 정제
    safe_main = re.sub(r"[^a-zA-Z0-9가-힣]", "", main_kw)[:10]
    safe_sub = re.sub(r"[^a-zA-Z0-9가-힣]", "", sub_kw)[:10]
    gen_key = uuid.uuid4().hex[:6]
    
    image_urls = []
    filenames = []
    for i in range(payload.image_count):
        fname = f"{safe_main}-{safe_sub}-{gen_key}-{i+1}.png"
        filenames.append(fname)
        image_urls.append(f"/generated_images/{fname}")

    new_post.image_paths = [] 
    new_post.expected_image_count = payload.image_count # 예상 이미지 수 저장
    db.commit()

    for i in range(payload.image_count):
        # 썸네일(마지막) 이미지인 경우 별도 처리
        if i == payload.image_count - 1:
            base_prompt = img_prompts[i] if i < len(img_prompts) else f"{payload.topic} blog thumbnail design"
            prompt = f"{base_prompt}, blog thumbnail, high resolution"
        else:
            prompt = img_prompts[i] if i < len(img_prompts) else f"{payload.topic} photography"
            
        background_tasks.add_task(
            process_image_generation, 
            post_id=new_post.id, 
            index=i + 1, 
            prompt=prompt, 
            filename=filenames[i]
        )

    return {
        "status": "processing",
        "image_total": payload.image_count,
        "post_id": new_post.id,
        "html": html_result["html"],
        "summary": html_result.get("summary", ""),
        "credits_required": credits_needed,
        "images": image_urls,
        "image_error": None,
    }


@router.post("/{post_id}/publish")
async def publish_manual_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 포스트를 해당 블로그 플랫폼에 즉시 발행합니다.
    """
    post = db.query(Post).join(Blog).filter(Post.id == post_id, Blog.owner_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다.")

    if post.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="이미 발행된 포스트입니다.")

    blog = post.blog
    # 발행에 필요한 데이터 구성
    html_result = {
        "title": post.title,
        "html": post.content,
        "thumbnail_url": post.thumbnail_url,
        "images": post.image_paths
    }

    try:
        result = await publish_post(blog, html_result)
        
        if result.get("status") == "published":
            post.status = "PUBLISHED"
            post.published_url = result.get("url")
            post.published_at = datetime.now()
            
            # 발행 성공 시 즉시 트래킹 시작
            post.tracking_status = "TRACKING"
            db.commit()
            
            try:
                await tracking_service.update_post_tracking(db, post_id)
                post.tracking_status = "COMPLETED"
                post.last_tracked_at = datetime.now()
                db.commit()
            except Exception as track_err:
                LOGGER.error(f"Auto-tracking failed after manual publish for post {post_id}: {track_err}")
                post.tracking_status = "PENDING"
                db.commit()

            return {"status": "success", "url": post.published_url}
        else:
            return {"status": "failed", "message": result.get("message", "발행 실패")}
            
    except Exception as e:
        LOGGER.exception(f"Manual publish failed for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=f"발행 실패: {str(e)}")


@router.post("/{post_id}/track")
async def trigger_post_tracking(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    특정 포스트의 순위 트래킹을 수동으로 트리거합니다.
    """
    post = db.query(Post).join(Blog).filter(Post.id == post_id, Blog.owner_id == current_user.id).first()
    if not post:
        raise HTTPException(status_code=404, detail="포스트를 찾을 수 없습니다.")
    
    if not post.published_url:
        raise HTTPException(status_code=400, detail="발행된 URL이 없어 트래킹할 수 없습니다.")

    post.tracking_status = "TRACKING"
    db.commit()
    
    # 실제 트래킹 시작
    await tracking_service.update_post_tracking(db, post_id)
    
    post.tracking_status = "COMPLETED"
    post.last_tracked_at = datetime.now()
    db.commit()
    
    return {"status": "ok", "keyword_ranks": post.keyword_ranks}


@router.get("/keywords")
def get_keyword_tracking(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    키워드 트래킹 테이블용 최소 엔드포인트.
    """
    blogs = db.query(Blog).options(joinedload(Blog.posts)).filter(Blog.owner_id == current_user.id).all()
    rows: list[dict] = []
    for blog in blogs:
        for post in blog.posts:
            ranks = post.keyword_ranks or {}
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
