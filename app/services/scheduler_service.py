import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import sql_models as models
from app.agents.writer import WriterAgent
from app.agents.publisher import PublisherAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.crawler import CrawlerAgent
# TO-BE: 키워드 큐 및 발행 API 연동
from app.services.keyword_service import get_next_keyword, mark_keyword_used
from app.services.publisher_api import publish_post
from app.services.gemini_service import generate_html
import logging

LOGGER = logging.getLogger(__name__)


async def generate_and_save_post(db: Session, user: models.User, config: models.BlogConfig):
    """
    TO-BE: 키워드 큐 기반 자동 포스팅 생성 및 발행
    
    1. 키워드 큐에서 다음 키워드 가져오기 (순환 로직)
    2. Gemini로 SEO 최적화 콘텐츠 생성
    3. 블로그 플랫폼 API로 자동 발행
    4. 키워드 사용 처리
    """
    LOGGER.info(f"[Process Start] User {user.email} / Category: {config.default_category}")
    
    target_blog = db.query(models.Blog).filter(models.Blog.owner_id == user.id).first()
    if not target_blog:
        LOGGER.error(f"[Error] No blog found for user {user.id}")
        return

    # 1. 키워드 큐에서 다음 키워드 가져오기
    keyword = get_next_keyword(db, user.id)
    if not keyword:
        keyword = config.default_category or "최신 트렌드"
        LOGGER.warning(f"키워드 큐가 비어있어 기본 카테고리 사용: {keyword}")
    
    LOGGER.info(f"[Keyword] 선택된 키워드: {keyword}")
    
    # 2. 크롤러로 최신 정보 수집 (선택)
    crawler = CrawlerAgent()
    knowledge_agent = KnowledgeAgent(db)
    crawled_summary = ""
    try:
        crawled_data = await crawler.fetch_latest_news(keyword)
        crawled_summary = await knowledge_agent.update_ontology(keyword, crawled_data)
        LOGGER.info("[Crawler] 온톨로지 업데이트 완료")
    except Exception as e:
        LOGGER.warning(f"[Crawler Error] {e}")
    
    # 3. Gemini로 SEO 최적화 콘텐츠 생성
    ontology_context = await knowledge_agent.search_ontology(query=keyword)
    full_context = f"{crawled_summary}\n{ontology_context}"
    
    custom_prompt = config.custom_prompt or f"{keyword} 주제로 SEO 최적화 블로그 글을 작성하세요."
    word_range = target_blog.word_range or {"min": 800, "max": 1200}
    image_count = target_blog.image_count or config.image_count or 3
    
    try:
        html_result = await generate_html(
            topic=keyword,
            persona=target_blog.persona or "전문 블로거",
            prompt=custom_prompt,
            word_count_range=(word_range.get("min", 800), word_range.get("max", 1200)),
            image_count=image_count,
            keywords=[keyword]
        )
        
        # 4. DB에 포스트 저장
        new_post = models.Post(
            blog_id=target_blog.id,
            title=html_result.get("title", "Untitled Auto Post"),
            content=html_result.get("html", ""),
            status="DRAFT",
            seo_title_length=html_result.get("seo_title_length"),
            meta_description_length=html_result.get("meta_description_length"),
            cta_text=html_result.get("cta_text"),
            expected_image_count=image_count,
            img_gen_status="PROCESSING"
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        LOGGER.info(f"[Post Created] ID {new_post.id} / Title: {new_post.title}")

        # 5. 이미지 생성 프로세스 (동기 방식으로 대기)
        from app.api.v1.posts import process_image_generation, validate_and_fix_image_prompts
        import uuid
        import re

        img_prompts = html_result.get("image_prompts") or []
        img_prompts, _ = validate_and_fix_image_prompts(keyword, img_prompts)
        
        gen_key = uuid.uuid4().hex[:6]
        safe_kw = re.sub(r"[^a-zA-Z0-9가-힣]", "", keyword)[:10]
        
        for i in range(image_count):
            fname = f"auto-{safe_kw}-{gen_key}-{i+1}.png"
            prompt = img_prompts[i] if i < len(img_prompts) else f"{keyword} photography"
            # 백그라운드 태스크 대신 직접 await 하여 완료를 기다림
            await process_image_generation(new_post.id, i+1, prompt, fname)
        
        # 최신 상태 리프레시 (이미지 생성 완료 대기)
        max_retries = 30 # 최대 5분 (10초 * 30)
        images_ready = False
        for _ in range(max_retries):
            db.refresh(new_post)
            if new_post.img_gen_status == "COMPLETED":
                images_ready = True
                break
            if new_post.img_gen_status in ["FAILED", "TIMEOUT"]:
                LOGGER.warning(f"이미지 생성 중 일부 오류 발생({new_post.img_gen_status}), 하지만 포스팅 시도")
                images_ready = True # 일부 실패해도 일단 진행
                break
            await asyncio.sleep(10)
        
        if not images_ready:
            LOGGER.error(f"이미지 생성 대기 시간 초과(5분). 자동 포스팅을 중단합니다. 포스트 ID: {new_post.id}")
            new_post.status = "PUBLISH_FAILED"
            new_post.img_gen_status = "TIMEOUT"
            db.commit()
            return
        
        # 6. 블로그 플랫폼 API로 자동 발행
        try:
            # 이미지 경로가 포함된 상태로 다시 구성
            publish_payload = {
                "title": new_post.title,
                "html": new_post.content,
                "images": new_post.image_paths or []
            }
            publish_result = await publish_post(target_blog, publish_payload)
            new_post.status = "PUBLISHED"
            new_post.published_url = publish_result.get("url")
            db.commit()
            LOGGER.info(f"[Published] {publish_result.get('platform')}: {publish_result.get('url')}")
        except Exception as e:
            LOGGER.error(f"[Publish Failed] {e}")
            new_post.status = "PUBLISH_FAILED"
            db.commit()
        
        # 7. 키워드 사용 처리
        mark_keyword_used(db, user.id, keyword)
        
    except Exception as e:
        db.rollback()
        LOGGER.error(f"[Fail] AI Generation failed: {str(e)}")


def process_scheduled_tasks(db: Session):
    now = datetime.now()
    current_time_str = now.strftime("%H:%M")
    current_day_str = now.strftime("%a").upper()
    print(f"[Scheduler] Checking tasks for {current_day_str} {current_time_str}...")

    schedules = db.query(models.ScheduleConfig).filter(models.ScheduleConfig.is_active == True).all()

    for schedule in schedules:
        if schedule.frequency == models.Frequency.WEEKLY:
            if not schedule.active_days or current_day_str not in schedule.active_days:
                continue

        if not schedule.target_times or current_time_str not in schedule.target_times:
            continue

        if schedule.last_run_at:
            last_run_str = schedule.last_run_at.strftime("%H:%M")
            last_run_day = schedule.last_run_at.strftime("%Y-%m-%d")
            if last_run_day == now.strftime("%Y-%m-%d") and last_run_str == current_time_str:
                continue

        user = schedule.user
        blog_config = user.blog_config
        if not blog_config:
            print(f" -> User {user.id} has no blog config. Skipping.")
            continue

        policy = db.query(models.SystemPolicy).first()
        if not policy:
            print(" -> System policy missing. Skipping.")
            continue

        cost = 0
        if blog_config.post_length == models.PostLength.SHORT:
            cost += policy.cost_short
        elif blog_config.post_length == models.PostLength.MEDIUM:
            cost += policy.cost_medium
        elif blog_config.post_length == models.PostLength.LONG:
            cost += policy.cost_long
        cost += policy.cost_image * blog_config.image_count

        if user.current_credit < cost:
            print(f" -> User {user.id} failed: Not enough credit ({user.current_credit} < {cost})")
            continue

        try:
            user.current_credit -= cost
            log = models.CreditLog(
                user_id=user.id,
                amount=-cost,
                action_type="AUTO_POSTING",
                details={
                    "time": current_time_str,
                    "length": blog_config.post_length,
                    "image_count": blog_config.image_count,
                },
            )
            db.add(log)
            schedule.last_run_at = now
            db.commit()
            print(f" -> User {user.id}: Credit deducted (-{cost}). Starting AI generation...")
            try:
                asyncio.run(generate_and_save_post(db, user, blog_config))
            except Exception as e:
                print(f"   [System Error] Async execution failed: {e}")
        except Exception as e:
            db.rollback()
            print(f" -> Error processing user {user.id}: {str(e)}")

