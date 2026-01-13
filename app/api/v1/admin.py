from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.sql_models import User, CreditLog, SystemPolicy, Post, Blog, PaymentRequest, RechargePlan, SystemConfig

router = APIRouter()

class ConfigUpdateRequest(BaseModel):
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    toss_link: Optional[str] = None
    kakao_link: Optional[str] = None

class RechargePlanCreate(BaseModel):
    name: str
    amount: int
    credits: int
    badge_text: Optional[str] = None
    is_popular: bool = False
    is_active: bool = True

class RechargePlanUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[int] = None
    credits: Optional[int] = None
    badge_text: Optional[str] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None

class PaymentConfirmRequest(BaseModel):
    request_id: int
    approve: bool # True: 승인, False: 거절


class ManualCreditGrantRequest(BaseModel):
    user_email: str
    amount: int
    reason: str


class PolicyUpdateRequest(BaseModel):
    signup_bonus: Optional[int] = None
    referral_bonus: Optional[int] = None
    cost_short: Optional[int] = None
    cost_medium: Optional[int] = None
    cost_long: Optional[int] = None
    cost_image: Optional[int] = None


@router.post("/credits/manual-grant")
async def manual_credit_grant(
    payload: ManualCreditGrantRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    관리자 수동 크레딧 지급
    
    TODO: 관리자 권한 검증 로직 추가 필요
    """
    # 관리자 권한 검증 (간단 예시: 특정 이메일만 허용)
    # if admin_user.email not in ["admin@example.com"]:
    #     raise HTTPException(403, "관리자 권한이 없습니다")
    
    user = db.query(User).filter(User.email == payload.user_email).first()
    if not user:
        raise HTTPException(404, "사용자를 찾을 수 없습니다")
    
    user.current_credit += payload.amount
    log = CreditLog(
        user_id=user.id,
        amount=payload.amount,
        action_type="MANUAL_GRANT",
        details={"reason": payload.reason, "admin": admin_user.email}
    )
    db.add(log)
    db.commit()
    
    return {
        "status": "ok",
        "user_email": user.email,
        "new_credit": user.current_credit,
        "granted_amount": payload.amount
    }


@router.post("/credits/confirm-payment")
async def confirm_payment(
    payload: PaymentConfirmRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    관리자 입금 확인 및 크레딧 지급 승인
    """
    req = db.query(PaymentRequest).filter(PaymentRequest.id == payload.request_id).first()
    if not req:
        raise HTTPException(404, "요청을 찾을 수 없습니다")
    
    if req.status != "PENDING":
        raise HTTPException(400, "이미 처리된 요청입니다")

    if payload.approve:
        user = db.query(User).filter(User.id == req.user_id).first()
        if user:
            user.current_credit += req.requested_credits
            req.status = "COMPLETED"
            
            # 크레딧 로그 업데이트
            log = CreditLog(
                user_id=user.id,
                amount=req.requested_credits,
                action_type="DEPOSIT_CONFIRMED",
                details={"request_id": req.id, "amount_krw": req.amount, "admin": admin_user.email}
            )
            db.add(log)
    else:
        req.status = "CANCELLED"

    db.commit()
    return {"status": "ok", "request_status": req.status}


@router.get("/credits/pending-payments")
async def get_pending_payments(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    대기 중인 입금 확인 요청 목록
    """
    pending = db.query(PaymentRequest).filter(PaymentRequest.status == "PENDING").order_by(PaymentRequest.created_at.asc()).all()
    return pending


@router.get("/policy")
async def get_policy(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    시스템 정책 조회
    """
    policy = db.query(SystemPolicy).first()
    if not policy:
        # 기본 정책 생성
        policy = SystemPolicy(
            signup_bonus=100,
            referral_bonus=50,
            cost_short=10,
            cost_medium=20,
            cost_long=30,
            cost_image=5
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    
    return {
        "signup_bonus": policy.signup_bonus,
        "referral_bonus": policy.referral_bonus,
        "cost_short": policy.cost_short,
        "cost_medium": policy.cost_medium,
        "cost_long": policy.cost_long,
        "cost_image": policy.cost_image,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
    }


@router.put("/policy")
async def update_policy(
    payload: PolicyUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    시스템 정책 업데이트
    """
    policy = db.query(SystemPolicy).first()
    if not policy:
        policy = SystemPolicy()
        db.add(policy)
    
    # 제공된 필드만 업데이트
    if payload.signup_bonus is not None:
        policy.signup_bonus = payload.signup_bonus
    if payload.referral_bonus is not None:
        policy.referral_bonus = payload.referral_bonus
    if payload.cost_short is not None:
        policy.cost_short = payload.cost_short
    if payload.cost_medium is not None:
        policy.cost_medium = payload.cost_medium
    if payload.cost_long is not None:
        policy.cost_long = payload.cost_long
    if payload.cost_image is not None:
        policy.cost_image = payload.cost_image
    
    db.commit()
    db.refresh(policy)
    
    return {
        "status": "ok",
        "message": "정책이 업데이트되었습니다",
        "policy": {
            "signup_bonus": policy.signup_bonus,
            "referral_bonus": policy.referral_bonus,
            "cost_short": policy.cost_short,
            "cost_medium": policy.cost_medium,
            "cost_long": policy.cost_long,
            "cost_image": policy.cost_image
        }
    }


@router.get("/config")
async def get_system_config(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    시스템 설정 조회 (입금 계좌 등)
    """
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.put("/config")
async def update_system_config(
    payload: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    시스템 설정 업데이트
    """
    config = db.query(SystemConfig).first()
    if not config:
        config = SystemConfig()
        db.add(config)
    
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(config, k, v)
    
    db.commit()
    db.refresh(config)
    return config


@router.get("/plans")
async def get_all_plans(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    모든 요금제 플랜 조회 (관리자용)
    """
    return db.query(RechargePlan).order_by(RechargePlan.amount.asc()).all()


@router.post("/plans")
async def create_plan(
    payload: RechargePlanCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    신규 요금제 플랜 생성
    """
    plan = RechargePlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    payload: RechargePlanUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    기존 요금제 플랜 수정
    """
    plan = db.query(RechargePlan).filter(RechargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "플랜을 찾을 수 없습니다")
    
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(plan, k, v)
    
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    요금제 플랜 삭제
    """
    plan = db.query(RechargePlan).filter(RechargePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "플랜을 찾을 수 없습니다")
    
    db.delete(plan)
    db.commit()
    return {"status": "ok"}


@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_user)
):
    """
    관리자 대시보드 통계
    """
    # 전체 사용자 수
    total_users = db.query(User).count()
    
    # 전체 블로그 수
    total_blogs = db.query(Blog).count()
    
    # 전체 포스트 수
    total_posts = db.query(Post).count()
    
    # 발행된 포스트 수
    published_posts = db.query(Post).filter(Post.status == "PUBLISHED").count()
    
    # 전체 크레딧 사용량 (수량 합계)
    total_credits_used = db.query(func.abs(func.sum(CreditLog.amount))).filter(CreditLog.amount < 0).scalar() or 0
    
    # 입금 대기 목록 (PaymentRequest 테이블 기준)
    pending_deposits = db.query(PaymentRequest).filter(PaymentRequest.status == "PENDING").count()
    
    return {
        "total_users": total_users,
        "total_blogs": total_blogs,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "total_credits_used": int(total_credits_used),
        "pending_deposits": pending_deposits
    }
