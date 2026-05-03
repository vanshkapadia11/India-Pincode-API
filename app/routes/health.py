from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.logger import logger
import httpx
import os
import time

router = APIRouter(prefix="/health", tags=["Health"])

# track server start time
START_TIME = time.time()


def get_uptime() -> str:
    seconds = int(time.time() - START_TIME)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}h {minutes}m {seconds}s"


async def check_db(db: Session) -> dict:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "connected"}
    except Exception as e:
        logger.error(f"DB health check failed: {str(e)}")
        return {"status": "error", "detail": str(e)}


async def check_gemini() -> dict:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return {"status": "reachable"}
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        logger.error(f"Gemini health check failed: {str(e)}")
        return {"status": "unreachable", "detail": str(e)}


@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    db_status = await check_db(db)
    gemini_status = await check_gemini()

    # overall status — ok only if both are healthy
    overall = (
        "ok"
        if (
            db_status["status"] == "connected"
            and gemini_status["status"] == "reachable"
        )
        else "degraded"
    )

    return {
        "status": overall,
        "uptime": get_uptime(),
        "version": "1.0.0",
        "services": {
            "database": db_status,
            "gemini": gemini_status,
        },
    }


@router.get("/ping")
def ping():
    # lightweight check — no DB or Gemini call
    return {"status": "ok", "uptime": get_uptime()}
