from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from app.database import engine
from app import models
from app.routes import pincode, ai, keys, health
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.logging import LoggingMiddleware
from app.logger import logger
import time

# track start time
START_TIME = time.time()

# create all tables in DB automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pincode API",
    description="Indian Pincode lookup API with Gemini AI features",
    version="1.0.0",
)

# ─── Middleware ────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Rate Limiter ─────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ─── Routes ───────────────────────────────────────────────
app.include_router(pincode.router)
app.include_router(ai.router)
app.include_router(keys.router)
app.include_router(health.router)


# ─── Startup / Shutdown ───────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info("🚀 Pincode API starting up...")
    logger.info("✅ Database tables verified")
    logger.info("✅ Routes registered")
    logger.info("✅ Middleware attached")
    logger.info("📡 Server ready at http://localhost:8000")


@app.on_event("shutdown")
async def shutdown():
    uptime = int(time.time() - START_TIME)
    logger.info(f"🛑 Pincode API shutting down after {uptime}s uptime")


# ─── Root ─────────────────────────────────────────────────
@app.get("/", tags=["default"])
def root():
    return {
        "message": "Welcome to Pincode API 🇮🇳",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "lookup": "GET  /pincode/{pincode}",
            "validate": "GET  /pincode/validate/{pincode}",
            "search": "GET  /pincode/search/query?q=&page=1&per_page=20",
            "by_state": "GET  /pincode/state/{state}?page=1&per_page=20",
            "by_district": "GET  /pincode/district/{district}?page=1&per_page=20",
            "bulk_lookup": "POST /pincode/bulk",
            "distance": "GET  /pincode/distance/calculate?from_pincode=&to_pincode=",
            "nearby": "GET  /pincode/nearby/search?pincode=&km=10",
            "serviceable": "GET  /pincode/serviceable/{pincode}",
            "suggest": "GET  /pincode/suggest/query?q=",
            "cache_stats": "GET  /pincode/cache/stats",
            "parse_address": "POST /ai/parse-address",
            "delivery_estimate": "POST /ai/delivery-estimate",
            "create_key": "POST /keys/create",
            "list_keys": "GET  /keys/list",
            "revoke_key": "DELETE /keys/revoke/{name}",
            "key_stats": "GET  /keys/stats/{name}",
            "health": "GET  /health",
            "ping": "GET  /health/ping",
        },
    }


@app.get("/health/ping", tags=["default"])
def ping():
    uptime = int(time.time() - START_TIME)
    return {"status": "ok", "uptime": f"{uptime}s"}
