from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import sql_models as models
from app.schemas import BlogConfigUpdate, ScheduleConfigUpdate, SystemPolicyUpdate

router = APIRouter()


# --- [사용자: 블로그 작성 설정]
@router.put("/blog-settings")
def update_blog_settings(
    config: BlogConfigUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    settings = (
        db.query(models.BlogConfig)
        .filter(models.BlogConfig.user_id == current_user.id)
        .first()
    )
    if not settings:
        settings = models.BlogConfig(user_id=current_user.id)
        db.add(settings)

    settings.default_category = config.category
    settings.custom_prompt = config.custom_prompt
    settings.post_length = config.post_length
    settings.image_count = config.image_count

    db.commit()
    return {"msg": "Settings updated", "data": config}


# --- [사용자: 스케줄링 설정]
@router.put("/schedule")
def update_schedule(
    config: ScheduleConfigUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if config.target_times and len(config.target_times) != config.posts_per_day:
        raise HTTPException(
            status_code=400,
            detail="Count of target_times must match posts_per_day"
        )

    schedule = (
        db.query(models.ScheduleConfig)
        .filter(models.ScheduleConfig.user_id == current_user.id)
        .first()
    )
    if not schedule:
        schedule = models.ScheduleConfig(user_id=current_user.id)
        db.add(schedule)

    schedule.is_active = config.is_active
    schedule.frequency = config.frequency
    schedule.active_days = config.active_days
    schedule.posts_per_day = config.posts_per_day
    schedule.target_times = config.target_times

    db.commit()
    return {"msg": "Schedule updated"}


# --- [사용자: 견적 조회]
@router.get("/estimate")
def get_estimate(length: str, image_count: int, db: Session = Depends(get_db)):
    policy = db.query(models.SystemPolicy).first()
    if not policy:
        raise HTTPException(status_code=500, detail="System policy missing")

    cost = 0
    if length == "SHORT":
        cost += policy.cost_short
    elif length == "MEDIUM":
        cost += policy.cost_medium
    elif length == "LONG":
        cost += policy.cost_long

    cost += policy.cost_image * image_count
    return {"estimated_credit": cost}


# --- [관리자: 정책 설정]
@router.put("/admin/policy")
def update_policy(policy_data: SystemPolicyUpdate, db: Session = Depends(get_db)):
    policy = db.query(models.SystemPolicy).filter(models.SystemPolicy.id == 1).first()
    if not policy:
        policy = models.SystemPolicy(id=1)
        db.add(policy)

    for key, value in policy_data.dict().items():
        setattr(policy, key, value)

    db.commit()
    return {"msg": "Policy updated"}

