from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_api_key_or_ip(request: Request) -> str:
    # rate limit by API key if present, otherwise by IP
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return api_key
    return get_remote_address(request)


# create limiter instance
limiter = Limiter(key_func=get_api_key_or_ip)


# custom error response when rate limit is hit
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded.",
            "error": str(exc.detail),
            "hint": "Max 60 requests per minute per API key.",
        },
    )
