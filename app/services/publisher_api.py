"""
블로그 플랫폼 API 발행 서비스

TO-BE 요구사항:
- 구글 블로거 API v3 연동
- 티스토리 OAuth API 연동
- 인블로그 커스텀 API 연동 (제공 시)
- 네이버: HTML 생성 후 수동 발행 (API 없음)
"""

import os
import logging
from typing import Dict, Optional
import httpx
from app.models.sql_models import Blog
from app.core.config import settings

LOGGER = logging.getLogger(__name__)


async def publish_to_blogger(blog: Blog, html_result: Dict) -> Dict:
    """
    구글 블로거 API v3를 통한 포스트 발행
    
    Args:
        blog: Blog 모델 (blog_id, api_key_data 포함)
        html_result: Gemini 생성 결과 (title, html, meta_description 등)
    
    Returns:
        Dict: 발행 결과 (url, id 등)
    """
    if not blog.blog_id or not blog.api_key_data:
        raise ValueError("블로거 API 설정이 필요합니다 (blog_id, access_token)")
    
    access_token = blog.api_key_data.get("access_token")
    if not access_token:
        raise ValueError("블로거 access_token이 없습니다")
    
    url = f"https://www.googleapis.com/blogger/v3/blogs/{blog.blog_id}/posts/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "kind": "blogger#post",
        "title": html_result.get("title", "제목 없음"),
        "content": html_result.get("html", ""),
        "labels": html_result.get("meta_keywords", [])
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            result = resp.json()
        
        LOGGER.info(f"블로거 발행 성공: {result.get('url')}")
        return {
            "platform": "Blogger",
            "status": "published",
            "url": result.get("url"),
            "post_id": result.get("id")
        }
    
    except httpx.HTTPStatusError as e:
        LOGGER.error(f"블로거 API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        raise
    except Exception as e:
        LOGGER.error(f"블로거 발행 실패: {e}")
        raise


async def publish_to_tistory(blog: Blog, html_result: Dict) -> Dict:
    """
    티스토리 OAuth API를 통한 포스트 발행
    
    Args:
        blog: Blog 모델 (blog_id=블로그명, api_key_data 포함)
        html_result: Gemini 생성 결과
    
    Returns:
        Dict: 발행 결과
    """
    if not blog.blog_id or not blog.api_key_data:
        raise ValueError("티스토리 API 설정이 필요합니다 (blog_id=블로그명, access_token)")
    
    access_token = blog.api_key_data.get("access_token")
    if not access_token:
        raise ValueError("티스토리 access_token이 없습니다")
    
    url = "https://www.tistory.com/apis/post/write"
    params = {
        "access_token": access_token,
        "output": "json",
        "blogName": blog.blog_id,
        "title": html_result.get("title", "제목 없음"),
        "content": html_result.get("html", ""),
        "visibility": "3",  # 0=비공개, 1=보호, 3=발행
        "category": "0",  # 카테고리 ID (선택)
        "tag": ",".join(html_result.get("meta_keywords", []))
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, params=params)
            resp.raise_for_status()
            result = resp.json()
        
        if result.get("tistory", {}).get("status") == "200":
            post_id = result["tistory"]["postId"]
            post_url = result["tistory"]["url"]
            LOGGER.info(f"티스토리 발행 성공: {post_url}")
            return {
                "platform": "Tistory",
                "status": "published",
                "url": post_url,
                "post_id": post_id
            }
        else:
            error_msg = result.get("tistory", {}).get("error_message", "알 수 없는 오류")
            raise RuntimeError(f"티스토리 API 오류: {error_msg}")
    
    except httpx.HTTPStatusError as e:
        LOGGER.error(f"티스토리 API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        raise
    except Exception as e:
        LOGGER.error(f"티스토리 발행 실패: {e}")
        raise


async def publish_to_inblog(blog: Blog, html_result: Dict) -> Dict:
    """
    인블로그 커스텀 API를 통한 포스트 발행
    
    Args:
        blog: Blog 모델
        html_result: Gemini 생성 결과 (title, html, image_prompts, thumbnail_url 등)
    
    Returns:
        Dict: 발행 결과
    """
    api_key = settings.INBLOG_API_KEY
    writer_id = settings.INBLOG_WRITER_ID

    if not api_key:
        # 블로그별 api_key_data에 개별 키가 있을 수도 있으므로 체크
        api_key = blog.api_key_data.get("api_key") if blog.api_key_data else None
    
    if not api_key:
        raise ValueError("인블로그 API Key가 설정되지 않았습니다 (INBLOG_API_KEY)")

    # 인블로그 API 엔드포인트
    url = "https://api.inblog.ai/v1/posts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Gemini 생성 결과에서 썸네일 URL 추출
    thumbnail_url = html_result.get("thumbnail_url")
    if not thumbnail_url and html_result.get("images"):
        thumbnail_url = html_result["images"][0]

    payload = {
        "title": html_result.get("title", "제목 없음"),
        "content": html_result.get("html", ""),
        "status": "published",
        "writerId": writer_id or blog.blog_id,
        "thumbnail": thumbnail_url
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            result = resp.json()
        
        post_url = result.get("url") or f"https://inblog.ai/post/{result.get('id')}"
        LOGGER.info(f"인블로그 발행 성공: {post_url}")
        
        return {
            "platform": "InBlog",
            "status": "published",
            "url": post_url,
            "post_id": result.get("id")
        }
    
    except httpx.HTTPStatusError as e:
        LOGGER.error(f"인블로그 API 오류 (HTTP {e.response.status_code}): {e.response.text}")
        raise
    except Exception as e:
        LOGGER.error(f"인블로그 발행 실패: {e}")
        raise


async def publish_to_naver(blog: Blog, html_result: Dict) -> Dict:
    """
    네이버 블로그 (API 없음 - HTML 생성만)
    
    네이버는 공식 API가 없으므로 HTML을 생성하여 DB에 저장하고,
    사용자가 수동으로 복사/붙여넣기 하도록 안내
    
    Args:
        blog: Blog 모델
        html_result: Gemini 생성 결과
    
    Returns:
        Dict: HTML 저장 결과
    """
    LOGGER.info("네이버 블로그는 API가 없어 HTML만 생성합니다")
    return {
        "platform": "Naver",
        "status": "html_ready",
        "message": "HTML이 생성되었습니다. 네이버 블로그에 수동으로 붙여넣기 해주세요.",
        "html": html_result.get("html", "")
    }


async def publish_post(blog: Blog, html_result: Dict) -> Dict:
    """
    플랫폼별 자동 발행 라우터
    
    Args:
        blog: Blog 모델
        html_result: Gemini 생성 결과
    
    Returns:
        Dict: 발행 결과
    """
    platform = blog.platform_type.lower()
    
    if platform == "blogger":
        return await publish_to_blogger(blog, html_result)
    elif platform == "tistory":
        return await publish_to_tistory(blog, html_result)
    elif platform == "inblog":
        return await publish_to_inblog(blog, html_result)
    elif platform == "naver":
        return await publish_to_naver(blog, html_result)
    else:
        raise ValueError(f"지원하지 않는 플랫폼: {platform}")
