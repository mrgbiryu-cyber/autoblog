from fastapi import FastAPI, Depends, HTTPException
from app.core.config import settings
from app.api.v1 import auth, blog, admin, dashboard
from app.agents.knowledge import KnowledgeAgent
from app.agents.writer import WriterAgent
from app.agents.seo_analyst import SEOAgent
from app.agents.publisher import PublisherAgent
from app.models.sql_models import UserBlog

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

# Include Routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(blog.router, prefix=f"{settings.API_V1_STR}/blog", tags=["blog"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])
app.include_router(dashboard.router, prefix=f"{settings.API_V1_STR}/dashboard", tags=["dashboard"])

# Initialize Agents
knowledge_agent = KnowledgeAgent()
writer_agent = WriterAgent()
seo_agent = SEOAgent()
publisher_agent = PublisherAgent()

# Helper to get blog info (Mock)
async def get_blog_info(blog_id: int):
    # In reality, fetch from DB
    # mock object
    class MockBlog:
        id = blog_id
        platform_type = "WordPress"
        current_tier = 2
        persona_prompt = "Friendly Tech Expert"
        config = {}
    return MockBlog()

@app.post("/generate-content/{blog_id}")
async def create_automated_post(blog_id: int):
    # 0. Load Blog Info
    blog = await get_blog_info(blog_id)
    
    # 1. Agent 1: Knowledge & Topic Selection
    topic = await knowledge_agent.get_personalized_topic(blog)
    
    # 2. Agent 2: Content Generation
    draft = await writer_agent.write_content(topic, blog.persona_prompt)
    
    # 3. Agent 3: SEO Analysis & Verification
    seo_report = await seo_agent.analyze(draft, platform=blog.platform_type, tier=blog.current_tier)
    
    if seo_report.needs_rewrite:
        draft = await writer_agent.rewrite(draft, seo_report.feedback)
        
    # 4. Agent 4: Publishing
    result = await publisher_agent.execute(draft, blog.config)
    
    return {"status": "success", "data": result}

@app.get("/")
async def root():
    return {"message": "Welcome to AI Blog SaaS API"}
