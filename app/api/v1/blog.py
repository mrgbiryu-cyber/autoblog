from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def create_blog():
    return {"message": "Create blog endpoint"}

@router.get("/{blog_id}")
async def get_blog(blog_id: int):
    return {"message": f"Get blog {blog_id}"}
