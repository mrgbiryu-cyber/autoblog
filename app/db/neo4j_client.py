import logging
from urllib.parse import urlparse

from neo4j import GraphDatabase, Session

from app.core.config import settings

LOGGER = logging.getLogger("neo4j_client")


def _normalize_neo4j_uri(uri: str) -> str:
    """
    AS-IS: docker 환경에서 흔히 쓰는 bolt://neo4j:7687 로 설정될 수 있는데,
    GCP 단독 실행에서는 'neo4j' 호스트가 resolve되지 않아 ServiceUnavailable이 발생합니다.
    TO-BE: 호스트가 'neo4j'면 bolt://localhost:7687 로 강제 폴백합니다.
    """
    try:
        parsed = urlparse(uri)
        if parsed.hostname == "neo4j":
            fallback = f"{parsed.scheme}://localhost:{parsed.port or 7687}"
            LOGGER.warning("NEO4J_URI host 'neo4j' is not resolvable here. Fallback -> %s", fallback)
            return fallback
    except Exception:
        # 파싱 실패 시 원본 사용
        return uri
    return uri


NEO4J_URI = _normalize_neo4j_uri(settings.NEO4J_URI)
NEO4J_USER = settings.NEO4J_USER
NEO4J_PASSWORD = settings.NEO4J_PASSWORD

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def get_db():
    session = driver.session()
    try:
        yield session
    finally:
        session.close()

