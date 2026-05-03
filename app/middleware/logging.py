import time
import uuid
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # generate unique request ID
        request_id = str(uuid.uuid4())[:8]

        # record start time
        start_time = time.time()

        # get API key from header if present
        api_key = request.headers.get("X-API-Key", "anonymous")
        key_label = api_key[:10] + "..." if len(api_key) > 10 else api_key

        # log incoming request
        logger.info(
            f"→ REQUEST  | id:{request_id} | {request.method} {request.url.path} | key:{key_label}"
        )

        # process request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(
                f"✗ ERROR    | id:{request_id} | {request.method} {request.url.path} | error:{str(e)}"
            )
            raise e

        # calculate response time
        process_time = (time.time() - start_time) * 1000  # ms

        # log response
        logger.info(
            f"← RESPONSE | id:{request_id} | {request.method} {request.url.path} | status:{response.status_code} | {process_time:.2f}ms"
        )

        # add headers to response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{process_time:.2f}ms"

        return response
