from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    subscription_tier = Column(String(20), default='Starter')
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    blogs = relationship("UserBlog", back_populates="owner")

class UserBlog(Base):
    __tablename__ = "user_blogs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform_type = Column(String(20))
    blog_url = Column(Text, nullable=False)
    api_key_data = Column(JSON)
    current_tier = Column(Integer, default=1)
    daily_visitors = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="blogs")
    presets = relationship("UserPreset", back_populates="blog", uselist=False)
    posts = relationship("Post", back_populates="blog")
    sync_logs = relationship("CrawlSyncLog", back_populates="blog")

class UserPreset(Base):
    __tablename__ = "user_presets"

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("user_blogs.id"))
    persona_prompt = Column(Text)
    target_audience = Column(String(100))
    category_keywords = Column(JSON) # Storing array as JSON for simplicity in generic SQL
    style_preference = Column(String(50))

    blog = relationship("UserBlog", back_populates="presets")

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("user_blogs.id"))
    target_keyword = Column(String(100))
    title = Column(Text)
    content = Column(Text)
    seo_score = Column(Integer)
    status = Column(String(20))
    published_at = Column(DateTime(timezone=True))

    blog = relationship("UserBlog", back_populates="posts")
    seo_analytics = relationship("SEOAnalytics", back_populates="post", uselist=False)

class SEOAnalytics(Base):
    __tablename__ = "seo_analytics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"))
    rank_position = Column(Integer)
    estimated_revenue = Column(DECIMAL(10, 2))
    captured_at = Column(DateTime(timezone=True), server_default=func.now())

    post = relationship("Post", back_populates="seo_analytics")

class CrawlSyncLog(Base):
    __tablename__ = "crawl_sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    blog_id = Column(Integer, ForeignKey("user_blogs.id"))
    last_synced_at = Column(DateTime(timezone=True))
    new_entities_count = Column(Integer)

    blog = relationship("UserBlog", back_populates="sync_logs")
