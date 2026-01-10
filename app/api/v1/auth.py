from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models import sql_models as models
from app.schemas import UserCreate, Token
from datetime import timedelta
import secrets

router = APIRouter()

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    policy = db.query(models.SystemPolicy).filter(models.SystemPolicy.id == 1).first()
    if not policy:
        policy = models.SystemPolicy(id=1)
        db.add(policy)
        db.commit()
        db.refresh(policy)

    my_referral_code = secrets.token_hex(4).upper()

    new_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        my_referral_code=my_referral_code,
        current_credit=policy.signup_bonus,
        referred_by=user.referral_code
    )
    db.add(new_user)

    db.add(models.CreditLog(
        user=new_user,
        amount=policy.signup_bonus,
        action_type="SIGNUP_BONUS"
    ))

    if user.referral_code:
        inviter = db.query(models.User)\
            .filter(models.User.my_referral_code == user.referral_code).first()
        if inviter:
            inviter.current_credit += policy.referral_bonus
            db.add(models.CreditLog(
                user_id=inviter.id,
                amount=policy.referral_bonus,
                action_type="REFERRAL_REWARD",
                details={"invitee": user.email}
            ))

    db.commit()
    db.refresh(new_user)
    return {"msg": "User created successfully", "email": new_user.email}

@router.post("/login", response_model=Token)
def login(user_data: UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    if not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=60)
    )
    return {"access_token": access_token, "token_type": "bearer"}
