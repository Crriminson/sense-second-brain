from fastapi import APIRouter
from engine import process

router = APIRouter()

# REST API endpoints (for webapp + testing)

@router.post("/message")
async def send_message(message: str):
    response = process.process_text(message)
    return {"response": response}

@router.get("/status")
async def status():
    return {"status": "ok"}
