from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, EmailStr

# 1. 회원가입/로그인 요청 데이터
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str  # [추가] 이름 필드

# 2. 응답 데이터 (비밀번호 제외)
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    credits: int  # [추가]
    subscription_tier: str
    
    class Config:
        from_attributes = True

# 3. 토큰 응답 데이터
class Token(BaseModel):
    access_token: str
    token_type: str

# 4. 블로그 등록 요청 데이터
class BlogCreate(BaseModel):
    alias: str  # [추가] 관리자에서 볼 별칭
    platform_type: str  # Naver, Tistory 등
    blog_url: str       # https://blog.naver.com/id 또는 WP URL
    blog_id: str        # 네이버 아이디 또는 워드프레스 Username
    api_access_token: str | None = None  # 워드프레스/티스토리용 (네이버는 null)

# 5. 블로그 응답 데이터
class BlogResponse(BaseModel):
    id: int
    alias: str  # [추가]
    platform_type: str
    blog_url: str
    blog_id: str | None = None
    api_key_data: dict | None = None

    # 블로그별 저장 설정
    interest_topic: str | None = None
    persona: str | None = None
    default_category: str | None = None
    custom_prompt: str | None = None
    word_range: dict | None = None
    image_count: int | None = None

    class Config:
        from_attributes = True

# 6. 포스팅 성과 조회 데이터
class PostStatusResponse(BaseModel):
    id: int
    title: str
    status: str
    published_url: str | None
    view_count: int
    keyword_ranks: dict
    created_at: datetime

    class Config:
        from_attributes = True


# Policy / settings updates
class PostLengthEnum(str, Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class FrequencyEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class UserCreate(BaseModel):
    email: str
    password: str
    referral_code: Optional[str] = None


class BlogConfigUpdate(BaseModel):
    category: Optional[str] = None
    custom_prompt: Optional[str] = None
    post_length: PostLengthEnum
    image_count: int


class ScheduleConfigUpdate(BaseModel):
    is_active: bool
    frequency: FrequencyEnum
    active_days: Optional[List[str]] = None
    posts_per_day: int
    target_times: Optional[List[str]] = None


class SystemPolicyUpdate(BaseModel):
    signup_bonus: int
    referral_bonus: int
    cost_short: int
    cost_medium: int
    cost_long: int
    cost_image: int

