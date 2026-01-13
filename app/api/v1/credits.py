from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sql_models import User, PaymentRequest, CreditLog

router = APIRouter()

class PaymentRequestCreate(BaseModel):
    amount: int
    requested_credits: int
    depositor_name: str

class PaymentRequestResponse(BaseModel):
    id: int
    amount: int
    requested_credits: int
    status: str
    depositor_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/recharge/request", response_model=PaymentRequestResponse)
async def create_recharge_request(
    payload: PaymentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자가 송금 후 입금 확인 요청을 보냄
    """
    new_request = PaymentRequest(
        user_id=current_user.id,
        amount=payload.amount,
        requested_credits=payload.requested_credits,
        depositor_name=payload.depositor_name,
        status="PENDING"
    )
    db.add(new_request)
    
    # 관리자 확인용 로그 미리 생성 (통계용)
    log = CreditLog(
        user_id=current_user.id,
        amount=0, # 아직 지급 안됨
        action_type="DEPOSIT_PENDING",
        details={"amount": payload.amount, "credits": payload.requested_credits, "depositor": payload.depositor_name}
    )
    db.add(log)
    
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/recharge/history", response_model=List[PaymentRequestResponse])
async def get_recharge_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 충전 요청 내역 조회
    """
    return db.query(PaymentRequest).filter(PaymentRequest.user_id == current_user.id).order_by(PaymentRequest.created_at.desc()).all()

@router.get("/status")
async def get_credit_status(
    current_user: User = Depends(get_current_user)
):
    """
    현재 크레딧 잔액 조회 (SQL 기반)
    """
    return {
        "current_credit": current_user.current_credit,
        "upcoming_deduction": 0, # TODO: 예약된 포스팅에 따른 예상 차감액 계산 로직
        "currency": "KRW"
    }

