from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Blog SaaS"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/ai_blog_db"

    # Neo4j (Ontology)
    # NOTE: docker-compose 등에서 NEO4J_URI=bolt://neo4j:7687 로 들어오는 경우,
    # GCP 단독 실행 환경에선 'neo4j' 호스트가 resolve 되지 않아 장애가 나므로 기본값은 localhost로 둡니다.
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password1234"
    
    # Security
    SECRET_KEY: str = "supersecretkey"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Services
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()
