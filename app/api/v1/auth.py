from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
async def login():
    return {"message": "Login endpoint"}

@router.post("/signup")
async def signup():
    return {"message": "Signup endpoint"}
