from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


# [Enum 정의]
class Frequency(str, enum.Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class PostLength(str, enum.Enum):
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


# 1. [기존 User 수정] 추천인 및 크레딧 추가
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    current_credit = Column(Integer, default=0)
    my_referral_code = Column(String, unique=True, index=True)
    referred_by = Column(String, nullable=True)

    blogs = relationship("Blog", back_populates="owner")
    credit_logs = relationship("CreditLog", back_populates="user")
    blog_config = relationship("BlogConfig", uselist=False, back_populates="user")
    schedule_config = relationship("ScheduleConfig", uselist=False, back_populates="user")


# 2. [신규] 시스템 정책 (관리자용)
class SystemPolicy(Base):
    __tablename__ = "system_policy"

    id = Column(Integer, primary_key=True, index=True)
    signup_bonus = Column(Integer, default=100)
    referral_bonus = Column(Integer, default=50)
    cost_short = Column(Integer, default=10)
    cost_medium = Column(Integer, default=20)
    cost_long = Column(Integer, default=30)
    cost_image = Column(Integer, default=5)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())


# 3. [신규] 블로그 설정
class BlogConfig(Base):
    __tablename__ = "blog_config"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    default_category = Column(String, nullable=True)
    custom_prompt = Column(Text, nullable=True)
    post_length = Column(Enum(PostLength), default=PostLength.MEDIUM)
    image_count = Column(Integer, default=1)

    user = relationship("User", back_populates="blog_config")


# 4. [신규] 스케줄링 설정
class ScheduleConfig(Base):
    __tablename__ = "schedule_config"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    is_active = Column(Boolean, default=True)
    frequency = Column(Enum(Frequency), default=Frequency.DAILY)
    active_days = Column(JSON, nullable=True)
    posts_per_day = Column(Integer, default=1)
    target_times = Column(JSON, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="schedule_config")


# 5. [신규] 크레딧 로그
class CreditLog(Base):
    __tablename__ = "credit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    action_type = Column(String)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User", back_populates="credit_logs")


# 6. 기존 Blog/Post 유지 (필요 시 필드 확장)
class Blog(Base):
    __tablename__ = "blogs"
    id = Column(Integer, primary_key=True, index=True)
    # NOTE: 기존 코드 호환을 위해 title은 유지하되, 대시보드/프론트가 쓰는 필드를 추가합니다.
    title = Column(String, index=True, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    owner = relationship("User", back_populates="blogs")

    # Dashboard/blog management fields
    alias = Column(String, nullable=False, default="")
    platform_type = Column(String, nullable=False, default="Naver")
    blog_url = Column(String, nullable=False, default="")
    blog_id = Column(String, nullable=True)
    api_key_data = Column(JSON, nullable=True)
    status = Column(String, nullable=True, default="ACTIVE")

    # Blog-specific AI settings (per-blog 저장)
    interest_topic = Column(String, nullable=True)         # 사용자가 입력한 관심 주제
    persona = Column(String, nullable=True)                # 입력형 페르소나
    default_category = Column(String, nullable=True)       # 분석된/저장된 카테고리
    custom_prompt = Column(Text, nullable=True)            # 사용자가 수정한 작성 지시 프롬프트
    word_range = Column(JSON, nullable=True)               # {"min": 800, "max": 1200}
    image_count = Column(Integer, nullable=True)           # 블로그별 이미지 개수

    created_at = Column(DateTime(timezone=True), default=func.now())
    posts = relationship("Post", back_populates="blog")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("blogs.id"))
    blog = relationship("Blog", back_populates="posts")

    title = Column(String, nullable=False, default="")
    content = Column(Text, nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    published_url = Column(String, nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    keyword_ranks = Column(JSON, nullable=True)  # {"keyword": {"rank": 3, "change": 1, ...}, ...} 또는 자유 형식
    image_paths = Column(JSON, nullable=True)  # ["/generated_images/..png", ...]

    # TO-BE: SEO 최적화 필드
    seo_title_length = Column(Integer, nullable=True)
    meta_description_length = Column(Integer, nullable=True)
    cta_text = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    
    # [추가] 트래킹 관련
    tracking_status = Column(String, nullable=True, default="PENDING")
    last_tracked_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())


# 7. [신규] 온톨로지/지식 저장소
class Knowledge(Base):
    __tablename__ = "knowledge_base"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String, index=True)
    content = Column(Text)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())


# 8. [TO-BE] 키워드 큐 (순환 로직)
class KeywordQueue(Base):
    __tablename__ = "keyword_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    keyword = Column(String, nullable=False)
    priority = Column(Integer, default=0)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())

    user = relationship("User")


# 9. [TO-BE] 이미지 생성 큐
class ImageQueue(Base):
    __tablename__ = "image_queue"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    prompt = Column(Text, nullable=False)
    status = Column(String, default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    image_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    post = relationship("Post")


# 10. [신규] 결제/충전 요청 (수동 확인용)
class PaymentRequest(Base) :
    __tablename__ = "payment_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer, nullable=False) # 입금 금액 (원)
    requested_credits = Column(Integer, nullable=False) # 요청 크레딧
    status = Column(String, default="PENDING") # PENDING, COMPLETED, CANCELLED
    depositor_name = Column(String, nullable=True) # 입금자명
    created_at = Column(DateTime(timezone=True), default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())

    user = relationship("User")
