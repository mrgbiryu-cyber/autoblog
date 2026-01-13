"""
키워드 관리 API

TO-BE 요구사항:
- 키워드 검색 (네이버 API 연동)
- 키워드 벌크 등록
- 키워드 큐 조회
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sql_models import User, KeywordQueue
from app.services.keyword_service import (
    fetch_related_keywords,
    bulk_register_keywords,
    get_next_keyword
)

router = APIRouter()


class KeywordSearchResponse(BaseModel):
    keyword: str
    monthly_search: int
    competition: int
    priority: float


class KeywordBulkRegisterRequest(BaseModel):
    keywords: List[str]


@router.get("/search", response_model=List[KeywordSearchResponse])
async def search_keywords(
    seed: str,
    current_user: User = Depends(get_current_user)
):
    """
    키워드 리서치 API
    
    Args:
        seed: 시드 키워드
    
    Returns:
        List[KeywordSearchResponse]: 연관 키워드 목록
    """
    if not seed or len(seed.strip()) == 0:
        raise HTTPException(status_code=400, detail="시드 키워드를 입력해주세요")
    
    keywords = await fetch_related_keywords(seed.strip())
    return keywords


@router.post("/bulk-register")
async def bulk_register(
    payload: KeywordBulkRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    키워드 벌크 등록
    
    Args:
        payload: 키워드 리스트
    
    Returns:
        Dict: 등록 결과
    """
    if not payload.keywords or len(payload.keywords) == 0:
        raise HTTPException(status_code=400, detail="등록할 키워드가 없습니다")
    
    count = bulk_register_keywords(db, current_user.id, payload.keywords)
    return {
        "status": "ok",
        "registered_count": count,
        "message": f"{count}개 키워드가 등록되었습니다"
    }


@router.get("/queue")
async def get_keyword_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 키워드 큐 조회
    
    Returns:
        List[Dict]: 키워드 큐 목록
    """
    queue = db.query(KeywordQueue).filter(
        KeywordQueue.user_id == current_user.id
    ).order_by(KeywordQueue.priority.desc()).all()
    
    return [
        {
            "id": item.id,
            "keyword": item.keyword,
            "priority": item.priority,
            "used_at": item.used_at.isoformat() if item.used_at else None,
            "created_at": item.created_at.isoformat()
        }
        for item in queue
    ]


@router.get("/next")
async def get_next_keyword_api(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    다음 사용할 키워드 가져오기
    
    Returns:
        Dict: 다음 키워드
    """
    keyword = get_next_keyword(db, current_user.id)
    
    if not keyword:
        raise HTTPException(status_code=404, detail="사용 가능한 키워드가 없습니다")
    
    return {"keyword": keyword}
