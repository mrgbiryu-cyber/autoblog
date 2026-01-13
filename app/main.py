import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio

from app.core.database import init_db
# TO-BE: keywords 라우터 추가
from app.api.v1 import auth, blogs, posts, config, dashboard, keywords, admin, credits

# 우리가 만든 에이전트들 임포트
from app.agents.knowledge import KnowledgeAgent
from app.agents.writer import WriterAgent
from app.agents.seo_analyst import SEOAgent
from app.agents.publisher import PublisherAgent
from app.agents.reviewer import ReviewerAgent

app = FastAPI(title="Anti-Gravity Blog Engine")

# CORS 미들웨어 설정
cors_allow_origins = [o.strip() for o in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
cors_allow_origin_regex = os.getenv("CORS_ALLOW_ORIGIN_REGEX") or None
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allow_origins,
    allow_origin_regex=cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 생성된 이미지 폴더 정적 서빙
static_generated_dir = Path("static") / "generated_images"
static_generated_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/generated_images",
    StaticFiles(directory=str(static_generated_dir), check_dir=False),
    name="generated_images",
)

# 서버 시작 시 DB 테이블 자동 생성
init_db()

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(blogs.router, prefix="/api/v1/blogs", tags=["blogs"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(keywords.router, prefix="/api/v1/keywords", tags=["keywords"])  # TO-BE
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])  # TO-BE
app.include_router(credits.router, prefix="/api/v1/credits", tags=["credits"])

# 요청 받을 데이터 모델
class TopicRequest(BaseModel):
    category: str
    persona: str = "Friendly IT Expert"
    user_id: str = "admin"

@app.post("/generate-post")
async def generate_post_workflow(request: TopicRequest):
    print(f"\n🎬 Starting Workflow for Category: {request.category}")
    
    # 에이전트 초기화
    agent1 = KnowledgeAgent()
    agent2 = WriterAgent()
    agent3 = SEOAgent()
    agent4 = PublisherAgent()
    reviewer = ReviewerAgent()

    try:
        # Step 1: 주제 선정 (Agent 1)
        user_profile = {"category_keywords": [request.category], "persona_prompt": request.persona}
        topic_data = await agent1.get_optimized_topic(user_profile)
        if not topic_data:
            raise HTTPException(status_code=500, detail="Topic Generation Failed")
        
        # Step 2: 초안 작성 (Agent 2)
        draft = await agent2.write_content(topic_data, request.persona)

        # Step 2.5: Reviewer 1차 검수
        topic_title = topic_data.get("topic", request.category)
        review1 = reviewer.review_writer_output(draft, topic_title)
        if review1.cleaned_content is not None:
            draft["content"] = review1.cleaned_content
        if review1.cleaned_image_prompts is not None:
            draft["image_prompts"] = review1.cleaned_image_prompts
        
        # Step 3: SEO 검수 및 수정 루프
        max_retries = 2
        current_retry = 0
        
        while current_retry < max_retries:
            seo_result = await agent3.analyze(draft, topic_data, platform="Naver")
            
            if seo_result.get("pass", False):
                print(f"✅ SEO Passed! (Score: {seo_result['score']})")
                break
            
            print(f"⚠️ SEO Failed (Score: {seo_result['score']}). Requesting Rewrite {current_retry + 1}/{max_retries}...")
            print(f"   Feedback: {seo_result['feedback']}")
            
            draft = await agent2.rewrite(draft, seo_result['feedback'])
            current_retry += 1
            
        if not seo_result.get("pass", False):
            print("🚫 SEO Failed eventually, but publishing anyway (Time constraint).")

        # Step 4: 배포 및 후처리
        blog_config = {"platform_type": "Naver", "user_id": request.user_id, "ad_client_id": "demo-client"}
        final_result = await agent4.execute(draft, blog_config)

        # Step 4.5: Reviewer 최종 정제
        if isinstance(final_result, dict) and final_result.get("html"):
            review2 = reviewer.review_final_html(final_result["html"])
            if review2.cleaned_html:
                final_result["html"] = review2.cleaned_html
                final_result["review_issues"] = review2.issues
        
        return {
            "status": "success",
            "topic": topic_data,
            "seo_score": seo_result['score'],
            "published_info": final_result
        }

    except Exception as e:
        print(f"🔥 Workflow Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 자원 정리
        agent1.close()