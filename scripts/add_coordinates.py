import sys
import os
import time
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Pincode
from sqlalchemy import text

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "pincode-api/1.0"}


def get_coordinates(district: str, state: str) -> tuple:
    try:
        params = {"q": f"{district}, {state}, India", "format": "json", "limit": 1}
        response = httpx.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
        data = response.json()

        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None, None

    except Exception as e:
        print(f"  ⚠️  Error fetching {district}: {e}")
        return None, None


def add_coordinates():
    db = SessionLocal()

    try:
        # get all unique district + state combos
        pairs = db.execute(
            text("SELECT DISTINCT district, state FROM pincodes WHERE latitude IS NULL")
        ).fetchall()

        print(f"📍 Found {len(pairs)} unique districts to geocode\n")

        success = 0
        failed = 0

        for i, (district, state) in enumerate(pairs):
            if not district or not state:
                continue

            print(f"[{i+1}/{len(pairs)}] Fetching: {district}, {state}...", end=" ")

            lat, lng = get_coordinates(district, state)

            if lat and lng:
                # update all rows with this district+state
                db.execute(
                    text("""
                    UPDATE pincodes
                    SET latitude = :lat, longitude = :lng
                    WHERE district = :district AND state = :state
                """),
                    {"lat": lat, "lng": lng, "district": district, "state": state},
                )
                db.commit()
                print(f"✅ {lat:.4f}, {lng:.4f}")
                success += 1
            else:
                print("❌ Not found")
                failed += 1

            # Nominatim rate limit — 1 request per second (required!)
            time.sleep(1)

        print(f"\n🎉 Done! Success: {success} | Failed: {failed}")

    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    add_coordinates()
