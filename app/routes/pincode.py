from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    PincodeResponse,
    PostOffice,
    PaginatedResponse,
    BulkRequest,
    BulkResponse,
    CacheStats,
    DistanceResponse,
    DistancePoint,
    NearbyResponse,
    NearbyPincode,
    ServiceableResponse,
    SuggestResult,
)
from app.services import pincode_service, geo_service
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/pincode", tags=["Pincode"])


# ─── Single Lookup ────────────────────────────────────────
@router.get("/{pincode}", response_model=PincodeResponse)
@limiter.limit("60/minute")
def get_pincode(
    request: Request,
    pincode: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(
            status_code=400, detail="Invalid pincode format. Must be 6 digits."
        )

    results = pincode_service.get_by_pincode(db, pincode)
    if not results:
        raise HTTPException(status_code=404, detail=f"Pincode {pincode} not found.")

    return PincodeResponse(
        pincode=pincode,
        total_post_offices=len(results),
        post_offices=[PostOffice.from_orm(r) for r in results],
    )


# ─── Validate ─────────────────────────────────────────────
@router.get("/validate/{pincode}")
@limiter.limit("60/minute")
def validate_pincode(
    request: Request,
    pincode: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode format.")

    is_valid = pincode_service.validate_pincode(db, pincode)
    return {"pincode": pincode, "valid": is_valid}


# ─── Search ───────────────────────────────────────────────
@router.get("/search/query")
@limiter.limit("60/minute")
def search(
    request: Request,
    q: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search query too short.")

    result = pincode_service.search(db, q, page, per_page)

    return PaginatedResponse(
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        total_pages=result["total_pages"],
        results=[PostOffice.from_orm(r) for r in result["results"]],
    )


# ─── By State ─────────────────────────────────────────────
@router.get("/state/{state}")
@limiter.limit("30/minute")
def get_by_state(
    request: Request,
    state: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    result = pincode_service.get_by_state(db, state, page, per_page)

    if result["total"] == 0:
        raise HTTPException(
            status_code=404, detail=f"No pincodes found for state: {state}"
        )

    return PaginatedResponse(
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        total_pages=result["total_pages"],
        results=[PostOffice.from_orm(r) for r in result["results"]],
    )


# ─── By District ──────────────────────────────────────────
@router.get("/district/{district}")
@limiter.limit("30/minute")
def get_by_district(
    request: Request,
    district: str,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    result = pincode_service.get_by_district(db, district, page, per_page)

    if result["total"] == 0:
        raise HTTPException(
            status_code=404, detail=f"No pincodes found for district: {district}"
        )

    return PaginatedResponse(
        total=result["total"],
        page=result["page"],
        per_page=result["per_page"],
        total_pages=result["total_pages"],
        results=[PostOffice.from_orm(r) for r in result["results"]],
    )


# ─── Bulk Lookup ──────────────────────────────────────────
@router.post("/bulk", response_model=BulkResponse)
@limiter.limit("20/minute")
def bulk_lookup(
    request: Request,
    body: BulkRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    raw_results = pincode_service.get_bulk(db, body.pincodes)

    found = {}
    not_found = []

    for pincode, rows in raw_results.items():
        if rows:
            found[pincode] = PincodeResponse(
                pincode=pincode,
                total_post_offices=len(rows),
                post_offices=[PostOffice.from_orm(r) for r in rows],
            )
        else:
            not_found.append(pincode)

    return BulkResponse(
        total_requested=len(body.pincodes),
        total_found=len(found),
        total_not_found=len(not_found),
        results=found,
        not_found=not_found,
    )


# ─── Distance ─────────────────────────────────────────────
@router.get("/distance/calculate")
@limiter.limit("30/minute")
def get_distance(
    request: Request,
    from_pincode: str = Query(..., description="Origin pincode"),
    to_pincode: str = Query(..., description="Destination pincode"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(from_pincode) != 6 or not from_pincode.isdigit():
        raise HTTPException(
            status_code=400, detail=f"Invalid from_pincode: {from_pincode}"
        )
    if len(to_pincode) != 6 or not to_pincode.isdigit():
        raise HTTPException(status_code=400, detail=f"Invalid to_pincode: {to_pincode}")
    if from_pincode == to_pincode:
        raise HTTPException(
            status_code=400, detail="from_pincode and to_pincode cannot be the same."
        )

    result = geo_service.get_distance(db, from_pincode, to_pincode)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return DistanceResponse(
        from_=DistancePoint(
            pincode=result["from"]["pincode"],
            district=result["from"]["district"],
            state=result["from"]["state"],
            lat=result["from"]["lat"],
            lng=result["from"]["lng"],
        ),
        to=DistancePoint(
            pincode=result["to"]["pincode"],
            district=result["to"]["district"],
            state=result["to"]["state"],
            lat=result["to"]["lat"],
            lng=result["to"]["lng"],
        ),
        distance_km=result["distance_km"],
        distance_label=result["distance_label"],
    )


# ─── Nearby ───────────────────────────────────────────────
@router.get("/nearby/search")
@limiter.limit("20/minute")
def get_nearby(
    request: Request,
    pincode: str = Query(..., description="Origin pincode"),
    km: float = Query(default=10, ge=1, le=100, description="Radius in km (max 100)"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode format.")

    result = geo_service.get_nearby(db, pincode, km)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return NearbyResponse(
        origin_pincode=result["origin_pincode"],
        origin_district=result["origin_district"],
        origin_state=result["origin_state"],
        radius_km=result["radius_km"],
        total_found=result["total_found"],
        nearby=[NearbyPincode(**n) for n in result["nearby"]],
    )


# ─── Serviceable ──────────────────────────────────────────
@router.get("/serviceable/{pincode}", response_model=ServiceableResponse)
@limiter.limit("60/minute")
def check_serviceable(
    request: Request,
    pincode: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(pincode) != 6 or not pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode format.")

    result = geo_service.check_serviceable(db, pincode)
    return ServiceableResponse(**result)


# ─── Auto Suggest ─────────────────────────────────────────
@router.get("/suggest/query")
@limiter.limit("60/minute")
def suggest(
    request: Request,
    q: str = Query(..., min_length=2, description="Search prefix"),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    results = geo_service.suggest(db, q, limit)
    return {
        "query": q,
        "total": len(results),
        "suggestions": [SuggestResult(**r) for r in results],
    }


# ─── Cache Stats ──────────────────────────────────────────
@router.get("/cache/stats", response_model=CacheStats)
def cache_stats(_: dict = Depends(verify_api_key)):
    return pincode_service.get_cache_stats()
