from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def list_users():
    return {"message": "List users endpoint"}

@router.get("/stats")
async def system_stats():
    return {"message": "System stats endpoint"}
