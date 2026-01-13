import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    AS-IS: Pydantic v2 환경에서 BaseSettings는 pydantic-settings로 이동했는데,
           서버에 pydantic-settings가 없어서 import 단계에서 크래시(502 발생)했습니다.

    TO-BE: 외부 패키지에 의존하지 않고, 필요한 설정만 env에서 직접 읽는 경량 설정 객체로 교체합니다.
           (.env 로드는 각 모듈이 필요 시 python-dotenv를 사용하거나, 운영에선 system env로 주입)
    """

    PROJECT_NAME: str = "AI Blog SaaS"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ai_blog_db")

    # Neo4j (Ontology)
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password1234")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    # AI Services
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # inblog API
    INBLOG_API_KEY: str = os.getenv("INBLOG_API_KEY", "")
    INBLOG_WRITER_ID: str = os.getenv("INBLOG_WRITER_ID", "")


settings = Settings()
