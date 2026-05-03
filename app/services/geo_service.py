import math
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import Pincode
from app.services.cache_service import cache
from app.logger import logger


# ─── Haversine Formula ────────────────────────────────────
# calculates straight-line distance between two lat/lng points
def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # Earth radius in km

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return round(R * c, 2)


# ─── Get Coordinates for a Pincode ───────────────────────
def get_pincode_coords(db: Session, pincode: str):
    cache_key = f"coords:{pincode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    result = (
        db.query(Pincode)
        .filter(Pincode.pincode == pincode, Pincode.latitude.isnot(None))
        .first()
    )

    if not result:
        return None

    coords = {
        "lat": result.latitude,
        "lng": result.longitude,
        "district": result.district,
        "state": result.state,
    }

    cache.set(cache_key, coords, ttl=3600)  # cache for 1 hour
    return coords


# ─── Distance Between Two Pincodes ───────────────────────
def get_distance(db: Session, from_pincode: str, to_pincode: str) -> dict:
    cache_key = f"distance:{from_pincode}:{to_pincode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    from_coords = get_pincode_coords(db, from_pincode)
    to_coords = get_pincode_coords(db, to_pincode)

    if not from_coords:
        return {"error": f"Coordinates not found for pincode {from_pincode}"}
    if not to_coords:
        return {"error": f"Coordinates not found for pincode {to_pincode}"}

    distance = haversine(
        from_coords["lat"], from_coords["lng"], to_coords["lat"], to_coords["lng"]
    )

    result = {
        "from": {
            "pincode": from_pincode,
            "district": from_coords["district"],
            "state": from_coords["state"],
            "lat": from_coords["lat"],
            "lng": from_coords["lng"],
        },
        "to": {
            "pincode": to_pincode,
            "district": to_coords["district"],
            "state": to_coords["state"],
            "lat": to_coords["lat"],
            "lng": to_coords["lng"],
        },
        "distance_km": distance,
        "distance_label": f"{distance} km",
    }

    cache.set(cache_key, result, ttl=3600)
    return result


# ─── Nearby Pincodes ──────────────────────────────────────
def get_nearby(db: Session, pincode: str, radius_km: float = 10) -> dict:
    cache_key = f"nearby:{pincode}:{radius_km}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    origin = get_pincode_coords(db, pincode)
    if not origin:
        return {"error": f"Coordinates not found for pincode {pincode}"}

    # rough bounding box to filter candidates before haversine
    # 1 degree lat ≈ 111 km
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * math.cos(math.radians(origin["lat"])))

    candidates = db.execute(
        text("""
        SELECT DISTINCT pincode, district, state, latitude, longitude
        FROM pincodes
        WHERE latitude BETWEEN :min_lat AND :max_lat
          AND longitude BETWEEN :min_lng AND :max_lng
          AND pincode != :origin_pincode
          AND latitude IS NOT NULL
    """),
        {
            "min_lat": origin["lat"] - lat_delta,
            "max_lat": origin["lat"] + lat_delta,
            "min_lng": origin["lng"] - lng_delta,
            "max_lng": origin["lng"] + lng_delta,
            "origin_pincode": pincode,
        },
    ).fetchall()

    # now apply exact haversine filter
    nearby = []
    for row in candidates:
        dist = haversine(origin["lat"], origin["lng"], row.latitude, row.longitude)
        if dist <= radius_km:
            nearby.append(
                {
                    "pincode": row.pincode,
                    "district": row.district,
                    "state": row.state,
                    "distance_km": dist,
                }
            )

    # sort by distance closest first
    nearby.sort(key=lambda x: x["distance_km"])

    result = {
        "origin_pincode": pincode,
        "origin_district": origin["district"],
        "origin_state": origin["state"],
        "radius_km": radius_km,
        "total_found": len(nearby),
        "nearby": nearby,
    }

    cache.set(cache_key, result, ttl=600)
    return result


# ─── Serviceable Check ────────────────────────────────────
def check_serviceable(db: Session, pincode: str) -> dict:
    cache_key = f"serviceable:{pincode}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    results = db.query(Pincode).filter(Pincode.pincode == pincode).all()

    if not results:
        return {"pincode": pincode, "exists": False, "serviceable": False}

    delivery_offices = [r for r in results if r.delivery == "Delivery"]
    non_delivery = [r for r in results if r.delivery == "Non-Delivery"]

    result = {
        "pincode": pincode,
        "exists": True,
        "serviceable": len(delivery_offices) > 0,
        "total_post_offices": len(results),
        "delivery_offices": len(delivery_offices),
        "non_delivery_offices": len(non_delivery),
        "district": results[0].district,
        "state": results[0].state,
    }

    cache.set(cache_key, result, ttl=600)
    return result


# ─── Auto Suggest ─────────────────────────────────────────
def suggest(db: Session, q: str, limit: int = 10) -> list:
    if len(q) < 2:
        return []

    cache_key = f"suggest:{q.lower()}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    # search post offices and districts starting with query
    results = db.execute(
        text("""
        SELECT DISTINCT post_office, pincode, district, state
        FROM pincodes
        WHERE LOWER(post_office) LIKE LOWER(:q)
           OR LOWER(district) LIKE LOWER(:q)
        ORDER BY post_office
        LIMIT :limit
    """),
        {"q": f"{q}%", "limit": limit},
    ).fetchall()

    suggestions = [
        {
            "name": row.post_office,
            "pincode": row.pincode,
            "district": row.district,
            "state": row.state,
        }
        for row in results
    ]

    cache.set(cache_key, suggestions, ttl=300)
    return suggestions
