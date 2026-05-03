from pydantic import BaseModel, field_validator
from typing import List, Optional, Generic, TypeVar, Dict
from datetime import datetime

T = TypeVar("T")


# ─── Pagination ───────────────────────────────────────────
class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    per_page: int
    total_pages: int
    results: List[T]


# ─── Post Office ──────────────────────────────────────────
class PostOffice(BaseModel):
    post_office: str
    office_type: Optional[str]
    delivery: Optional[str]
    division: Optional[str]
    region: Optional[str]
    circle: Optional[str]
    taluk: Optional[str]
    district: Optional[str]
    state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True


# ─── Pincode ──────────────────────────────────────────────
class PincodeResponse(BaseModel):
    pincode: str
    total_post_offices: int
    post_offices: List[PostOffice]

    class Config:
        from_attributes = True


# ─── Bulk Lookup ──────────────────────────────────────────
class BulkRequest(BaseModel):
    pincodes: List[str]

    @field_validator("pincodes")
    @classmethod
    def validate_pincodes(cls, pincodes):
        if len(pincodes) == 0:
            raise ValueError("At least one pincode required.")
        if len(pincodes) > 50:
            raise ValueError("Max 50 pincodes per request.")
        for p in pincodes:
            if len(p) != 6 or not p.isdigit():
                raise ValueError(f"Invalid pincode: {p}. Must be 6 digits.")
        return pincodes


class BulkResponse(BaseModel):
    total_requested: int
    total_found: int
    total_not_found: int
    results: Dict[str, PincodeResponse]
    not_found: List[str]


# ─── Distance ─────────────────────────────────────────────
class DistancePoint(BaseModel):
    pincode: str
    district: Optional[str]
    state: Optional[str]
    lat: Optional[float]
    lng: Optional[float]


class DistanceResponse(BaseModel):
    from_: DistancePoint
    to: DistancePoint
    distance_km: float
    distance_label: str

    class Config:
        populate_by_name = True


# ─── Nearby ───────────────────────────────────────────────
class NearbyPincode(BaseModel):
    pincode: str
    district: Optional[str]
    state: Optional[str]
    distance_km: float


class NearbyResponse(BaseModel):
    origin_pincode: str
    origin_district: Optional[str]
    origin_state: Optional[str]
    radius_km: float
    total_found: int
    nearby: List[NearbyPincode]


# ─── Serviceable ──────────────────────────────────────────
class ServiceableResponse(BaseModel):
    pincode: str
    exists: bool
    serviceable: bool
    total_post_offices: Optional[int]
    delivery_offices: Optional[int]
    non_delivery_offices: Optional[int]
    district: Optional[str]
    state: Optional[str]


# ─── Suggest ──────────────────────────────────────────────
class SuggestResult(BaseModel):
    name: str
    pincode: str
    district: Optional[str]
    state: Optional[str]


# ─── AI ───────────────────────────────────────────────────
class AIAddressRequest(BaseModel):
    address: str


class AIAddressResponse(BaseModel):
    raw_address: str
    extracted_pincode: Optional[str]
    corrected_pincode: Optional[str]
    details: Optional[PincodeResponse]
    ai_message: str


class AIDeliveryRequest(BaseModel):
    pincode: str
    product_type: str


class AIDeliveryResponse(BaseModel):
    pincode: str
    product_type: str
    estimate: str


# ─── API Key ──────────────────────────────────────────────
class APIKeyCreate(BaseModel):
    name: str


class APIKeyResponse(BaseModel):
    key: str
    name: str
    is_active: bool
    requests_today: int
    total_requests: int
    created_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Cache ────────────────────────────────────────────────
class CacheStats(BaseModel):
    total_entries: int
    active_entries: int
    expired_entries: int
