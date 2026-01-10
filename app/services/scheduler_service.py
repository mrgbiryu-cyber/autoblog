import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import sql_models as models
from app.agents.writer import WriterAgent
from app.agents.publisher import PublisherAgent
from app.agents.knowledge import KnowledgeAgent
from app.agents.crawler import CrawlerAgent  # [신규] 크롤러


async def generate_and_save_post(db: Session, user: models.User, config: models.BlogConfig):
    print(f"   [Process Start] User {user.email} / Category: {config.default_category}")
    target_blog = db.query(models.Blog).filter(models.Blog.owner_id == user.id).first()
    if not target_blog:
        print(f"   [Error] No blog found for user {user.id}")
        return

    crawler = CrawlerAgent()
    knowledge_agent = KnowledgeAgent(db)
    search_keyword = config.default_category or config.custom_prompt[:30] or "latest trends"
    print(f"   [Crawler] Fetching latest trends for: {search_keyword}...")
    crawled_summary = ""
    try:
        crawled_data = await crawler.fetch_latest_news(search_keyword)
        crawled_summary = await knowledge_agent.update_ontology(search_keyword, crawled_data)
        print(f"   [Crawler] Updated ontology with new facts.")
    except Exception as e:
        print(f"   [Crawler Error] {e}")

    query = search_keyword
    print(f"   [Ontology] Retrieving context for: {query}...")
    ontology_context = await knowledge_agent.search_ontology(query=query)
    full_context = f"{crawled_summary}\n{ontology_context}"

    full_prompt = (
        f"Topic Category: {config.default_category}\n"
        f"User Instruction: {config.custom_prompt}\n"
        f"\n[Latest Facts & Context from Ontology]:\n{full_context}\n"
        f"Target Length: {config.post_length} (Detailed and rich content)\n"
        "Task: Write a blog post incorporating the latest information provided above."
    )

    writer = WriterAgent()
    try:
        generated_content = await writer.generate(prompt=full_prompt)

        image_url = None
        if config.image_count and config.image_count > 0:
            print(f"   [Image] Generating {config.image_count} placeholder image(s)...")
            image_url = "https://via.placeholder.com/800x400"

        new_post = models.Post(
            blog_id=target_blog.id,
            title=generated_content.get("title", "Untitled Auto Post"),
            content=generated_content.get("content", ""),
            status="DRAFT",
        )
        db.add(new_post)
        db.commit()
        print(f"   [Success] Post created: ID {new_post.id} / Title: {new_post.title}")
        # PublisherAgent could be used here to publish immediately if needed
    except Exception as e:
        db.rollback()
        print(f"   [Fail] AI Generation failed: {str(e)}")


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

