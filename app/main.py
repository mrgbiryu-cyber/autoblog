from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # [추가1] 이거 필요합니다
from pydantic import BaseModel
import asyncio

from app.core.database import init_db  # [추가]
from app.api.v1 import auth, blogs, posts, config  # config router

# 우리가 만든 에이전트들 임포트
from app.agents.knowledge import KnowledgeAgent
from app.agents.writer import WriterAgent
from app.agents.seo_analyst import SEOAgent
from app.agents.publisher import PublisherAgent

app = FastAPI(title="Anti-Gravity Blog Engine")

# [추가2] CORS 미들웨어 설정 (이걸 추가해야 프론트에서 접속 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# [중요] 서버 시작 시 DB 테이블 자동 생성
init_db()

# [중요] 라우터 등록 (auth API 연결)
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(blogs.router, prefix="/api/v1/blogs", tags=["blogs"])
app.include_router(posts.router, prefix="/api/v1/posts", tags=["posts"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])

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

    try:
        # Step 1: 주제 선정 (Agent 1)
        user_profile = {"category_keywords": [request.category], "persona_prompt": request.persona}
        topic_data = await agent1.get_optimized_topic(user_profile)
        if not topic_data:
            raise HTTPException(status_code=500, detail="Topic Generation Failed")
        
        # Step 2: 초안 작성 (Agent 2)
        draft = await agent2.write_content(topic_data, request.persona)
        
        # Step 3: SEO 검수 및 수정 루프 (Agent 3 <-> Agent 2)
        # [핵심] 여기가 형님이 찾으시던 '재수정 로직'입니다.
        max_retries = 2  # 무한 루프 방지를 위해 최대 2번만 수정 기회 부여
        current_retry = 0
        
        while current_retry < max_retries:
            seo_result = await agent3.analyze(draft, topic_data, platform="Naver")
            
            if seo_result.get("pass", False):
                print(f"✅ SEO Passed! (Score: {seo_result['score']})")
                break # 합격하면 루프 탈출
            
            # 불합격 시 수정 요청
            print(f"⚠️ SEO Failed (Score: {seo_result['score']}). Requesting Rewrite {current_retry + 1}/{max_retries}...")
            print(f"   Feedback: {seo_result['feedback']}")
            
            draft = await agent2.rewrite(draft, seo_result['feedback'])
            current_retry += 1
            
        if not seo_result.get("pass", False):
            print("🚫 SEO Failed eventually, but publishing anyway (Time constraint).")

        # Step 4: 배포 및 후처리 (Agent 4)
        blog_config = {"platform_type": "Naver", "user_id": request.user_id, "ad_client_id": "demo-client"}
        final_result = await agent4.execute(draft, blog_config)
        
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