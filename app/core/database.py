from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

# 로컬 개발용 SQLite (나중에 PostgreSQL로 주소만 바꾸면 됨)
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# DB 세션 가져오기 (의존성 주입용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 테이블 자동 생성 (서버 켜질 때 실행)
def init_db():
    Base.metadata.create_all(bind=engine)

