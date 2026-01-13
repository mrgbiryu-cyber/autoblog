from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.sql_models import Blog, User
from app.schemas import BlogCreate, BlogResponse
from app.core.deps import get_current_user
from app.services.gemini_service import analyze_blog

router = APIRouter()


class BlogUpdate(BaseModel):
    alias: str | None = None
    platform_type: str | None = None
    blog_url: str | None = None
    blog_id: str | None = None
    api_access_token: str | None = None

    # blog-specific settings
    interest_topic: str | None = None
    persona: str | None = None
    default_category: str | None = None
    custom_prompt: str | None = None
    word_range: dict | None = None
    image_count: int | None = None


class BlogAnalysisRequest(BaseModel):
    blog_id: int | None = None
    blog_url: str | None = None
    alias: str | None = None
    topic: str | None = None


class BlogAnalysisResponse(BaseModel):
    category: str
    prompt: str

# 1. 내 블로그 등록하기
@router.post("/", response_model=BlogResponse)
def create_blog(
    blog: BlogCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    # [로직 변경] 플랫폼별 데이터 저장 처리
    api_data = {}
    if blog.platform_type in ["WordPress", "Tistory"]:
        if not blog.api_access_token:
            raise HTTPException(status_code=400, detail="API 토큰이 필요합니다.")
        api_data = {"access_token": blog.api_access_token}

    new_blog = Blog(
        owner_id=current_user.id,
        title=blog.alias,
        alias=blog.alias,
        platform_type=blog.platform_type,
        blog_url=blog.blog_url,
        blog_id=blog.blog_id,
        api_key_data=api_data,
    )

    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

# 2. 내 블로그 목록 조회
@router.get("/", response_model=List[BlogResponse])
def read_blogs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return current_user.blogs


@router.post("/analyze", response_model=BlogAnalysisResponse)
async def analyze_blog_for_user(
    payload: BlogAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 등록 전(슬롯) 분석도 지원: blog_url이 들어오면 해당 URL로 분석
    if payload.blog_url:
        result = await analyze_blog(payload.blog_url, payload.alias or payload.blog_url, payload.topic)
        return BlogAnalysisResponse(category=result["category"], prompt=result["prompt"])

    query = db.query(Blog).filter(Blog.owner_id == current_user.id)
    if payload.blog_id:
        query = query.filter(Blog.id == payload.blog_id)

    blog = query.first()
    if not blog:
        raise HTTPException(status_code=404, detail="등록된 블로그가 없습니다.")

    result = await analyze_blog(blog.blog_url, blog.alias or blog.blog_url, payload.topic)
    return BlogAnalysisResponse(category=result["category"], prompt=result["prompt"])


@router.put("/{blog_id}", response_model=BlogResponse)
def update_blog(
    blog_id: int,
    payload: BlogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    blog = (
        db.query(Blog)
        .filter(Blog.owner_id == current_user.id, Blog.id == blog_id)
        .first()
    )
    if not blog:
        raise HTTPException(status_code=404, detail="블로그를 찾을 수 없습니다.")

    if payload.alias is not None:
        blog.alias = payload.alias
        blog.title = payload.alias
    if payload.platform_type is not None:
        blog.platform_type = payload.platform_type
    if payload.blog_url is not None:
        blog.blog_url = payload.blog_url
    if payload.blog_id is not None:
        blog.blog_id = payload.blog_id

    # Blog-specific AI settings (per blog)
    if payload.interest_topic is not None:
        blog.interest_topic = payload.interest_topic
    if payload.persona is not None:
        blog.persona = payload.persona
    if payload.default_category is not None:
        blog.default_category = payload.default_category
    if payload.custom_prompt is not None:
        blog.custom_prompt = payload.custom_prompt
    if payload.word_range is not None:
        blog.word_range = payload.word_range
    if payload.image_count is not None:
        blog.image_count = payload.image_count

    # 토큰은 WordPress/Tistory일 때만 저장(그 외는 빈 값)
    if payload.api_access_token is not None:
        if blog.platform_type in ["WordPress", "Tistory"] and payload.api_access_token:
            blog.api_key_data = {"access_token": payload.api_access_token}
        else:
            blog.api_key_data = {}

    db.commit()
    db.refresh(blog)
    return blog

