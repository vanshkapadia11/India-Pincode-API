from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import APIKey
from app.schemas import APIKeyCreate, APIKeyResponse
from app.middleware.auth import verify_api_key
import secrets

router = APIRouter(prefix="/keys", tags=["API Keys"])


def generate_key() -> str:
    # generates a secure random key like: pk_a3f9b2c1d4e5f6a7b8c9d0e1f2a3b4c5
    return f"pk_{secrets.token_hex(16)}"


@router.post("/create", response_model=APIKeyResponse)
def create_key(
    request: APIKeyCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),  # only master key can create keys
):
    # check if name already exists
    existing = db.query(APIKey).filter(APIKey.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Key with name '{request.name}' already exists."
        )

    new_key = APIKey(
        key=generate_key(),
        name=request.name,
        is_active=True,
        requests_today=0,
        total_requests=0,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key


@router.get("/list", response_model=list[APIKeyResponse])
def list_keys(
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),  # only master key can list keys
):
    keys = db.query(APIKey).all()
    return keys


@router.delete("/revoke/{key_name}")
def revoke_key(
    key_name: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),  # only master key can revoke
):
    db_key = db.query(APIKey).filter(APIKey.name == key_name).first()
    if not db_key:
        raise HTTPException(status_code=404, detail=f"Key '{key_name}' not found.")

    db_key.is_active = False
    db.commit()
    return {"message": f"Key '{key_name}' revoked successfully."}


@router.put("/activate/{key_name}")
def activate_key(
    key_name: str, db: Session = Depends(get_db), _: dict = Depends(verify_api_key)
):
    db_key = db.query(APIKey).filter(APIKey.name == key_name).first()
    if not db_key:
        raise HTTPException(status_code=404, detail=f"Key '{key_name}' not found.")

    db_key.is_active = True
    db.commit()
    return {"message": f"Key '{key_name}' activated successfully."}


@router.get("/stats/{key_name}", response_model=APIKeyResponse)
def key_stats(
    key_name: str, db: Session = Depends(get_db), _: dict = Depends(verify_api_key)
):
    db_key = db.query(APIKey).filter(APIKey.name == key_name).first()
    if not db_key:
        raise HTTPException(status_code=404, detail=f"Key '{key_name}' not found.")
    return db_key
