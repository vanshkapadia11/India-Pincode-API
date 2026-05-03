from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    AIAddressRequest,
    AIAddressResponse,
    AIDeliveryRequest,
    AIDeliveryResponse,
    PincodeResponse,
    PostOffice,
)
from app.services import pincode_service, gemini_service
from app.middleware.auth import verify_api_key
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/parse-address", response_model=AIAddressResponse)
@limiter.limit("20/minute")
async def parse_address(
    request: Request,
    body: AIAddressRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if not body.address or len(body.address) < 5:
        raise HTTPException(status_code=400, detail="Address too short.")

    try:
        ai_result = await gemini_service.parse_address(body.address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

    extracted_pincode = ai_result.get("pincode")
    message = ai_result.get("message", "")

    # if pincode found look it up in DB
    details = None
    if extracted_pincode and extracted_pincode != "null":
        results = pincode_service.get_by_pincode(db, extracted_pincode)
        if results:
            details = PincodeResponse(
                pincode=extracted_pincode,
                total_post_offices=len(results),
                post_offices=[PostOffice.from_orm(r) for r in results],
            )

    return AIAddressResponse(
        raw_address=body.address,
        extracted_pincode=extracted_pincode,
        corrected_pincode=extracted_pincode,
        details=details,
        ai_message=message,
    )


@router.post("/delivery-estimate", response_model=AIDeliveryResponse)
@limiter.limit("20/minute")
async def delivery_estimate(
    request: Request,
    body: AIDeliveryRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_api_key),
):
    if len(body.pincode) != 6 or not body.pincode.isdigit():
        raise HTTPException(status_code=400, detail="Invalid pincode format.")

    results = pincode_service.get_by_pincode(db, body.pincode)
    if not results:
        raise HTTPException(
            status_code=404, detail=f"Pincode {body.pincode} not found."
        )

    state = results[0].state
    district = results[0].district

    try:
        estimate = await gemini_service.delivery_estimate(
            pincode=body.pincode,
            state=state,
            district=district,
            product_type=body.product_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

    return AIDeliveryResponse(
        pincode=body.pincode, product_type=body.product_type, estimate=estimate
    )
