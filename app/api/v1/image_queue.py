"""
이미지 Queue 관리 API

TO-BE 요구사항:
- Queue 상태 조회
- 백그라운드 Worker 트리거
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sql_models import User
from app.services.image_queue_service import (
    get_queue_status,
    process_all_pending_queues
)

router = APIRouter()


@router.get("/queue/{post_id}")
async def get_image_queue_status(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    포스트의 이미지 생성 Queue 상태 조회
    
    Args:
        post_id: 포스트 ID
    
    Returns:
        dict: Queue 상태 정보
    """
    status = get_queue_status(db, post_id)
    return status


@router.post("/queue/process")
async def trigger_queue_processing(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    이미지 생성 Queue 처리 트리거 (백그라운드)
    
    Returns:
        dict: 처리 시작 메시지
    """
    background_tasks.add_task(process_all_pending_queues, db, max_concurrent=3)
    
    return {
        "status": "ok",
        "message": "이미지 생성 Queue 처리가 시작되었습니다"
    }
