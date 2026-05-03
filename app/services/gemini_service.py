import httpx
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Try models in order if one fails
MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


async def call_gemini(prompt: str, retries: int = 3) -> str:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    for model in MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"

        for attempt in range(retries):
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(url, json=payload)

                if response.status_code == 429:
                    wait = 5 * (attempt + 1)  # 5s, 10s, 15s
                    print(f"[{model}] Rate limited, retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if response.status_code == 503:
                    print(f"[{model}] Unavailable, trying next model...")
                    break  # try next model

                if response.status_code == 200:
                    data = response.json()
                    return data["candidates"][0]["content"]["parts"][0]["text"]

                print(f"[{model}] Error {response.status_code}, trying next model...")
                break  # try next model

    raise Exception("All Gemini models failed. Try again in a minute.")


async def parse_address(address: str) -> dict:
    prompt = f"""
    Extract the pincode from this Indian address. If there is a typo, correct it.
    Address: "{address}"
    
    Reply in this exact JSON format only, no extra text:
    {{
        "pincode": "extracted or corrected pincode or null if not found",
        "message": "short explanation"
    }}
    """
    result = await call_gemini(prompt)

    import json

    clean = result.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


async def delivery_estimate(
    pincode: str, state: str, district: str, product_type: str
) -> str:
    prompt = f"""
    You are a smart Indian logistics assistant.
    Given the following details, estimate the delivery time and give useful info.
    
    Pincode: {pincode}
    State: {state}
    District: {district}
    Product Type: {product_type}
    
    Reply in 2-3 sentences. Mention estimated delivery days, 
    any regional considerations, and recommended courier if possible.
    """
    result = await call_gemini(prompt)
    return result.strip()
