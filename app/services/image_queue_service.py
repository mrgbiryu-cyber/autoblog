"""
이미지 생성 Queue 처리 서비스

TO-BE 요구사항:
- 이미지 생성 요청을 Queue에 등록
- 백그라운드 Worker가 순차적으로 처리
- 프론트엔드에서 Queue 상태 폴링
"""

import asyncio
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.sql_models import ImageQueue, Post
from app.services.image_service import generate_image_sync, save_image_bytes, WORKFLOW_PATH

LOGGER = logging.getLogger(__name__)


def enqueue_image_generation(db: Session, post_id: int, prompts: list[str]) -> list[int]:
    """
    이미지 생성 요청을 Queue에 등록
    
    Args:
        db: DB 세션
        post_id: 포스트 ID
        prompts: 이미지 프롬프트 리스트
    
    Returns:
        list[int]: 생성된 Queue ID 리스트
    """
    queue_ids = []
    for idx, prompt in enumerate(prompts):
        queue_entry = ImageQueue(
            post_id=post_id,
            prompt=prompt,
            status="PENDING"
        )
        db.add(queue_entry)
        db.flush()
        queue_ids.append(queue_entry.id)
    
    db.commit()
    LOGGER.info(f"Post {post_id}에 {len(prompts)}개 이미지 생성 요청 등록")
    return queue_ids


async def process_image_queue(db: Session, queue_id: int):
    """
    Queue에서 이미지 생성 처리
    
    Args:
        db: DB 세션
        queue_id: Queue ID
    """
    queue_entry = db.query(ImageQueue).filter(ImageQueue.id == queue_id).first()
    if not queue_entry or queue_entry.status != "PENDING":
        return
    
    # 상태 업데이트: PROCESSING
    queue_entry.status = "PROCESSING"
    db.commit()
    
    try:
        # 이미지 생성
        image_bytes = await generate_image_sync(WORKFLOW_PATH, queue_entry.prompt)
        filename = f"queue_{queue_id}_{int(datetime.now().timestamp())}.png"
        image_url = save_image_bytes(filename, image_bytes)
        
        # 상태 업데이트: COMPLETED
        queue_entry.status = "COMPLETED"
        queue_entry.image_url = image_url
        queue_entry.completed_at = datetime.now()
        
        # Post에 이미지 URL 추가
        post = db.query(Post).filter(Post.id == queue_entry.post_id).first()
        if post:
            image_paths = post.image_paths or []
            if image_url not in image_paths:
                image_paths.append(image_url)
                post.image_paths = image_paths
        
        db.commit()
        LOGGER.info(f"Queue {queue_id} 이미지 생성 완료: {image_url}")
        
    except Exception as e:
        # 상태 업데이트: FAILED
        queue_entry.status = "FAILED"
        queue_entry.error_message = str(e)
        db.commit()
        LOGGER.error(f"Queue {queue_id} 이미지 생성 실패: {e}")


def get_queue_status(db: Session, post_id: int) -> dict:
    """
    포스트의 이미지 생성 Queue 상태 조회
    
    Args:
        db: DB 세션
        post_id: 포스트 ID
    
    Returns:
        dict: Queue 상태 정보
    """
    queues = db.query(ImageQueue).filter(ImageQueue.post_id == post_id).all()
    
    total = len(queues)
    pending = sum(1 for q in queues if q.status == "PENDING")
    processing = sum(1 for q in queues if q.status == "PROCESSING")
    completed = sum(1 for q in queues if q.status == "COMPLETED")
    failed = sum(1 for q in queues if q.status == "FAILED")
    
    images = [
        {
            "id": q.id,
            "status": q.status,
            "url": q.image_url,
            "error": q.error_message
        }
        for q in queues
    ]
    
    return {
        "total": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "images": images
    }


async def process_all_pending_queues(db: Session, max_concurrent: int = 3):
    """
    모든 PENDING 상태의 Queue를 처리 (백그라운드 Worker용)
    
    Args:
        db: DB 세션
        max_concurrent: 동시 처리 개수
    """
    pending_queues = db.query(ImageQueue).filter(
        ImageQueue.status == "PENDING"
    ).limit(max_concurrent).all()
    
    if not pending_queues:
        return
    
    LOGGER.info(f"{len(pending_queues)}개 이미지 생성 Queue 처리 시작")
    
    tasks = [process_image_queue(db, q.id) for q in pending_queues]
    await asyncio.gather(*tasks, return_exceptions=True)
