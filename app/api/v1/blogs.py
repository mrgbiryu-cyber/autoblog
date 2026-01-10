from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.sql_models import Blog, User
from app.schemas import BlogCreate, BlogResponse
from app.core.deps import get_current_user

router = APIRouter()

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
        user_id=current_user.id,
        alias=blog.alias,
        platform_type=blog.platform_type,
        blog_url=blog.blog_url,
        blog_id=blog.blog_id,
        api_key_data=api_data
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

