from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from app.database import get_db
from app.models import APIKey
import os

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
MASTER_API_KEY = os.getenv("MASTER_API_KEY")


async def verify_api_key(
    api_key: str = Security(API_KEY_HEADER), db: Session = Depends(get_db)
):
    # no key provided
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key missing. Add X-API-Key header.",
        )

    # master key — always works, no DB check needed
    if api_key == MASTER_API_KEY:
        return {"name": "master", "key": api_key}

    # look up key in DB
    db_key = (
        db.query(APIKey).filter(APIKey.key == api_key, APIKey.is_active == True).first()
    )

    if not db_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or inactive API key."
        )

    # update usage stats
    db_key.total_requests += 1
    db_key.requests_today += 1
    db_key.last_used_at = func.now()
    db.commit()

    return {"name": db_key.name, "key": api_key}
