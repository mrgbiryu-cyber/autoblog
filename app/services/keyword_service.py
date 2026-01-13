"""
키워드 전략 시스템 - 네이버 검색광고 API 연동

TO-BE 요구사항:
- 연관 키워드, 서브 키워드, 월간 조회수 수집
- 키워드 우선순위 계산 (조회수 × 경쟁도 역수)
- 키워드 큐 관리 (벌크 등록, 순환 로직)
"""

import os
import logging
from typing import List, Dict, Optional
import httpx
from sqlalchemy.orm import Session
from app.models.sql_models import KeywordQueue

LOGGER = logging.getLogger(__name__)

# 네이버 검색광고 API 설정
NAVER_API_CLIENT_ID = os.getenv("NAVER_API_CLIENT_ID")
NAVER_API_CLIENT_SECRET = os.getenv("NAVER_API_CLIENT_SECRET")
NAVER_API_BASE_URL = "https://api.naver.com/keywordstool"


async def fetch_related_keywords(seed_keyword: str) -> List[Dict]:
    """
    네이버 검색광고 API를 통해 연관 키워드 수집
    
    Args:
        seed_keyword: 시드 키워드
    
    Returns:
        List[Dict]: 키워드 목록 (keyword, monthly_search, competition, priority)
    """
    if not NAVER_API_CLIENT_ID or not NAVER_API_CLIENT_SECRET:
        LOGGER.warning("네이버 API 키가 설정되지 않았습니다. 더미 데이터를 반환합니다.")
        return _generate_dummy_keywords(seed_keyword)
    
    headers = {
        "X-Naver-Client-Id": NAVER_API_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_API_CLIENT_SECRET,
        "Content-Type": "application/json"
    }
    
    # 네이버 검색광고 API 스펙에 맞게 조정 필요
    # 실제 API 문서: https://api.naver.com/keywordstool
    params = {
        "hintKeywords": seed_keyword,
        "showDetail": "1"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(NAVER_API_BASE_URL, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
        
        keywords = []
        for item in data.get("keywordList", []):
            monthly_pc = item.get("monthlyPcQcCnt", 0)
            monthly_mobile = item.get("monthlyMobileQcCnt", 0)
            monthly_total = monthly_pc + monthly_mobile
            competition = item.get("compIdx", 1)
            
            # 우선순위 계산: 조회수 / 경쟁도
            priority = monthly_total / max(competition, 1)
            
            keywords.append({
                "keyword": item.get("relKeyword", ""),
                "monthly_search": monthly_total,
                "competition": competition,
                "priority": round(priority, 2)
            })
        
        # 우선순위 정렬 (높은 순)
        keywords.sort(key=lambda x: x["priority"], reverse=True)
        return keywords
    
    except httpx.HTTPStatusError as e:
        LOGGER.error(f"네이버 API 호출 실패 (HTTP {e.response.status_code}): {e}")
        return _generate_dummy_keywords(seed_keyword)
    except Exception as e:
        LOGGER.error(f"키워드 수집 중 오류: {e}")
        return _generate_dummy_keywords(seed_keyword)


def _generate_dummy_keywords(seed_keyword: str) -> List[Dict]:
    """API 키가 없을 때 더미 데이터 생성"""
    return [
        {"keyword": f"{seed_keyword} 추천", "monthly_search": 12000, "competition": 50, "priority": 240.0},
        {"keyword": f"{seed_keyword} 방법", "monthly_search": 8500, "competition": 60, "priority": 141.67},
        {"keyword": f"{seed_keyword} 가이드", "monthly_search": 6000, "competition": 40, "priority": 150.0},
        {"keyword": f"{seed_keyword} 팁", "monthly_search": 5000, "competition": 30, "priority": 166.67},
        {"keyword": f"최고의 {seed_keyword}", "monthly_search": 4500, "competition": 70, "priority": 64.29},
    ]


def bulk_register_keywords(db: Session, user_id: int, keywords: List[str]) -> int:
    """
    키워드 벌크 등록
    
    Args:
        db: DB 세션
        user_id: 사용자 ID
        keywords: 키워드 리스트
    
    Returns:
        int: 등록된 키워드 개수
    """
    count = 0
    for idx, keyword in enumerate(keywords):
        # 중복 체크
        exists = db.query(KeywordQueue).filter(
            KeywordQueue.user_id == user_id,
            KeywordQueue.keyword == keyword
        ).first()
        
        if not exists:
            entry = KeywordQueue(
                user_id=user_id,
                keyword=keyword,
                priority=len(keywords) - idx  # 순서대로 우선순위 부여
            )
            db.add(entry)
            count += 1
    
    db.commit()
    LOGGER.info(f"사용자 {user_id}에게 {count}개 키워드 등록 완료")
    return count


def get_next_keyword(db: Session, user_id: int) -> Optional[str]:
    """
    다음 사용할 키워드 가져오기 (순환 로직)
    
    Args:
        db: DB 세션
        user_id: 사용자 ID
    
    Returns:
        Optional[str]: 다음 키워드 (없으면 None)
    """
    # 1. 미사용 키워드 중 우선순위 높은 것 선택
    entry = db.query(KeywordQueue).filter(
        KeywordQueue.user_id == user_id,
        KeywordQueue.used_at.is_(None)
    ).order_by(KeywordQueue.priority.desc()).first()
    
    if entry:
        return entry.keyword
    
    # 2. 모든 키워드 소진 시 재가동 (무한 루프)
    LOGGER.info(f"사용자 {user_id}의 키워드 큐 소진 → 재가동")
    db.query(KeywordQueue).filter(
        KeywordQueue.user_id == user_id
    ).update({"used_at": None})
    db.commit()
    
    # 3. 재가동 후 다시 선택
    entry = db.query(KeywordQueue).filter(
        KeywordQueue.user_id == user_id,
        KeywordQueue.used_at.is_(None)
    ).order_by(KeywordQueue.priority.desc()).first()
    
    return entry.keyword if entry else None


def mark_keyword_used(db: Session, user_id: int, keyword: str):
    """
    키워드 사용 처리
    
    Args:
        db: DB 세션
        user_id: 사용자 ID
        keyword: 사용한 키워드
    """
    from datetime import datetime
    
    entry = db.query(KeywordQueue).filter(
        KeywordQueue.user_id == user_id,
        KeywordQueue.keyword == keyword,
        KeywordQueue.used_at.is_(None)
    ).first()
    
    if entry:
        entry.used_at = datetime.now()
        db.commit()
        LOGGER.info(f"키워드 '{keyword}' 사용 처리 완료")
