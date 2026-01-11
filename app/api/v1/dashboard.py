from datetime import datetime

from fastapi import APIRouter, Depends
from neo4j import Session
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.db.neo4j_client import get_db
from app.models.sql_models import User

router = APIRouter()


class SchedulePayload(BaseModel):
    frequency: str
    posts_per_day: int
    days: list[str]
    target_times: list[str]


@router.get("/credits/status")
async def get_credit_status(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    query = """
    MERGE (u:User {user_id: $user_id})
    WITH u
    OPTIONAL MATCH (u)-[:HAS_CREDIT]->(c:Credit)
    RETURN c.amount AS amount, c.last_updated AS last_updated
    LIMIT 1
    """
    result = session.run(query, user_id=current_user.id)
    record = result.single()
    if record and record["amount"] is not None:
        return {
            "current_credit": record["amount"],
            "upcoming_deduction": 6,
            "currency": "KRW",
        }

    return {
        "current_credit": 42,
        "upcoming_deduction": 6,
        "currency": "KRW",
    }


@router.post("/schedule")
async def save_schedule(
    payload: SchedulePayload,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    query = """
    MERGE (u:User {user_id: $user_id})
    SET u.email = $email
    MERGE (u)-[:SCHEDULED]->(s:Schedule {user_id: $user_id})
    SET s.frequency = $frequency,
        s.posts_per_day = $posts_per_day,
        s.days = $days,
        s.target_times = $target_times,
        s.updated_at = $updated_at
    RETURN s
    """
    session.run(
        query,
        user_id=current_user.id,
        email=current_user.email,
        frequency=payload.frequency,
        posts_per_day=payload.posts_per_day,
        days=payload.days,
        target_times=payload.target_times,
        updated_at=datetime.utcnow().isoformat(),
    )
    return {"message": "스케줄이 성공적으로 저장되었습니다."}
from fastapi import APIRouter

router = APIRouter()

@router.get("/summary")
async def get_summary():
    return {"message": "Dashboard summary endpoint"}
