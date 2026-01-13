import httpx
from bs4 import BeautifulSoup
import logging
from sqlalchemy.orm import Session
from app.models.sql_models import Post
from typing import Dict, List, Optional, Any
import asyncio

logger = logging.getLogger(__name__)

class TrackingService:
    """
    발행된 포스팅의 검색 순위 및 상태를 추적하는 서비스 (V6)
    """

    async def get_naver_search_rank(self, keyword: str, target_url: str) -> Dict[str, Any]:
        """
        네이버 통합검색에서 특정 키워드로 검색했을 때 target_url의 순위를 확인합니다.
        """
        if not keyword or not target_url:
            return {"rank": -1, "status": "invalid_input"}

        search_url = f"https://search.naver.com/search.naver?query={keyword}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
                response = await client.get(search_url, headers=headers)
                if response.status_code != 200:
                    return {"rank": -1, "status": "blocked", "http_code": response.status_code}

                soup = BeautifulSoup(response.text, "html.parser")
                
                # 네이버 통합검색 결과 내 링크들을 수집 (VIEW, 블로그, 스마트블록 등)
                # 네이버의 HTML 구조는 자주 변경되므로 여러 패턴을 확인합니다.
                found_rank = -1
                
                # 1. api_link_all (주로 스마트블록/VIEW)
                links = soup.select("a.api_link_all, a.link_tit, a.total_tit")
                
                for idx, link in enumerate(links):
                    href = link.get("href", "")
                    if target_url in href:
                        found_rank = idx + 1
                        break
                
                if found_rank > 0:
                    return {"rank": found_rank, "status": "success"}
                else:
                    return {"rank": 100, "status": "not_found_top_100"}

        except Exception as e:
            logger.error(f"Naver rank tracking error: {str(e)}")
            return {"rank": -1, "status": "error", "message": str(e)}

    async def update_post_tracking(self, db: Session, post_id: int):
        """
        특정 포스트의 순위 정보를 갱신합니다.
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post or not post.published_url:
            return

        # 키워드 추출 (keyword_ranks JSON 필드에 저장된 키워드들 혹은 제목의 앞단)
        keywords_to_track = []
        if post.keyword_ranks and isinstance(post.keyword_ranks, dict):
            keywords_to_track = list(post.keyword_ranks.keys())
        
        if not keywords_to_track:
            # 제목에서 앞 20자 정도를 검색어로 사용 (임시)
            keywords_to_track = [post.title[:20].strip()]

        updated_ranks = {}
        for kw in keywords_to_track:
            result = await self.get_naver_search_rank(kw, post.published_url)
            updated_ranks[kw] = result
            # 루프 사이 딜레이 (IP 차단 방지)
            await asyncio.sleep(1)

        post.keyword_ranks = updated_ranks
        db.commit()

tracking_service = TrackingService()

