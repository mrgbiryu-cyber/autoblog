import os

# NOTE:
# 운영 환경에 `pydantic-settings`가 설치되어 있지 않은 경우가 있어도
# 서버가 부팅 단계에서 크래시하지 않도록 안전하게 import 합니다.
try:
    from pydantic_settings import BaseSettings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    # Pydantic v1 환경 (pydantic.BaseSettings)
    from pydantic import BaseSettings  # type: ignore

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Blog SaaS"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ai_blog_db")

    # Neo4j (Ontology)
    # NOTE: docker-compose 등에서 NEO4J_URI=bolt://neo4j:7687 로 들어오는 경우,
    # GCP 단독 실행 환경에선 'neo4j' 호스트가 resolve 되지 않아 장애가 나므로 기본값은 localhost로 둡니다.
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
    
    class Config:
        env_file = ".env"

settings = Settings()
