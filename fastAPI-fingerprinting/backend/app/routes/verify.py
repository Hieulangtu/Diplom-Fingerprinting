from fastapi import APIRouter, Request

verify_router = APIRouter()

@verify_router.get("/verify")
async def verify(req: Request):
    # Chỉ cần đi qua middleware là đủ
    return {"ok": True}

