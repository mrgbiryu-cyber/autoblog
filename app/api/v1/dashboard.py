from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sql_models import User, ScheduleConfig, Frequency

router = APIRouter()


class SchedulePayload(BaseModel):
    frequency: str
    posts_per_day: int
    days: list[str]
    target_times: list[str]
    is_active: bool = True


@router.get("/schedule")
async def get_schedule(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SQL DB에서 사용자의 스케줄 설정을 조회합니다.
    """
    config = db.query(ScheduleConfig).filter(ScheduleConfig.user_id == current_user.id).first()
    if not config:
        return None

    return {
        "frequency": config.frequency.lower(),
        "posts_per_day": config.posts_per_day,
        "days": config.active_days or [],
        "target_times": config.target_times or [],
        "is_active": config.is_active
    }


@router.post("/schedule")
async def save_schedule(
    payload: SchedulePayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    사용자의 스케줄 설정을 SQL DB에 저장하거나 업데이트합니다.
    """
    config = db.query(ScheduleConfig).filter(ScheduleConfig.user_id == current_user.id).first()
    
    # Enum 변환
    freq_map = {
        "hourly": Frequency.DAILY, # 현재 시스템상 최소단위는 DAILY 내 횟수
        "daily": Frequency.DAILY,
        "weekly": Frequency.WEEKLY
    }
    
    if not config:
        config = ScheduleConfig(
            user_id=current_user.id,
            is_active=payload.is_active,
            frequency=freq_map.get(payload.frequency, Frequency.DAILY),
            active_days=payload.days,
            posts_per_day=payload.posts_per_day,
            target_times=payload.target_times
        )
        db.add(config)
    else:
        config.is_active = payload.is_active
        config.frequency = freq_map.get(payload.frequency, Frequency.DAILY)
        config.active_days = payload.days
        config.posts_per_day = payload.posts_per_day
        config.target_times = payload.target_times
        config.last_run_at = None # 설정 변경 시 초기화(선택)

    try:
        db.commit()
        return {"message": "스케줄이 성공적으로 저장되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"스케줄 저장 실패: {str(e)}")
