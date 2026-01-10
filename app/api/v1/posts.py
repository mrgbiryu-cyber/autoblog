from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.core.database import get_db
from app.models.sql_models import Post, Blog, User
from app.schemas import PostStatusResponse
from app.core.deps import get_current_user
from pydantic import BaseModel

router = APIRouter()

# 블로그별 포스팅 현황을 묶어서 보여주기 위한 응답 구조
class BlogStatsResponse(BaseModel):
    blog_alias: str
    platform: str
    posts: List[PostStatusResponse]

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

