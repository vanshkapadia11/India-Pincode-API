from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Pincode
from app.services.cache_service import cache
import math


# ─── Helpers ──────────────────────────────────────────────
def paginate(query, page: int, per_page: int) -> dict:
    total = query.count()
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    results = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "results": results,
    }


# ─── Pincode Lookup ───────────────────────────────────────
def get_by_pincode(db: Session, pincode: str):
    # check cache first
    cache_key = f"pincode:{pincode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # query DB
    results = db.query(Pincode).filter(Pincode.pincode == pincode).all()

    # store in cache for 10 minutes
    if results:
        cache.set(cache_key, results, ttl=600)

    return results


# ─── Validate ─────────────────────────────────────────────
def validate_pincode(db: Session, pincode: str) -> bool:
    # check cache first
    cache_key = f"validate:{pincode}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = db.query(Pincode).filter(Pincode.pincode == pincode).first() is not None

    # cache for 10 minutes
    cache.set(cache_key, result, ttl=600)
    return result


# ─── Search ───────────────────────────────────────────────
def search(db: Session, q: str, page: int = 1, per_page: int = 20) -> dict:
    # search is not cached since queries are too varied
    query = db.query(Pincode).filter(
        Pincode.post_office.ilike(f"%{q}%")
        | Pincode.district.ilike(f"%{q}%")
        | Pincode.state.ilike(f"%{q}%")
        | Pincode.pincode.ilike(f"%{q}%")
    )
    return paginate(query, page, per_page)


# ─── By State ─────────────────────────────────────────────
def get_by_state(db: Session, state: str, page: int = 1, per_page: int = 20) -> dict:
    # cache first page of popular states
    cache_key = f"state:{state.lower()}:p{page}:pp{per_page}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    query = db.query(Pincode).filter(Pincode.state.ilike(f"%{state}%"))
    result = paginate(query, page, per_page)

    # cache for 5 minutes
    cache.set(cache_key, result, ttl=300)
    return result


# ─── By District ──────────────────────────────────────────
def get_by_district(
    db: Session, district: str, page: int = 1, per_page: int = 20
) -> dict:
    cache_key = f"district:{district.lower()}:p{page}:pp{per_page}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    query = db.query(Pincode).filter(Pincode.district.ilike(f"%{district}%"))
    result = paginate(query, page, per_page)

    # cache for 5 minutes
    cache.set(cache_key, result, ttl=300)
    return result


# ─── Bulk Lookup ──────────────────────────────────────────
def get_bulk(db: Session, pincodes: list[str]) -> dict:
    results = {}

    for pincode in pincodes:
        # try cache first
        cache_key = f"pincode:{pincode}"
        cached = cache.get(cache_key)

        if cached:
            results[pincode] = cached
            continue

        # query DB
        rows = db.query(Pincode).filter(Pincode.pincode == pincode).all()

        if rows:
            cache.set(cache_key, rows, ttl=600)
            results[pincode] = rows
        else:
            results[pincode] = []

    return results


# ─── Cache Stats ──────────────────────────────────────────
def get_cache_stats() -> dict:
    return cache.stats()
