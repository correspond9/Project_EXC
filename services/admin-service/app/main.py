from fastapi import FastAPI

from .routers.admin import router
from .routers.market import router as market_router
from .routers.fees import router as fees_router
from .routers.performance import router as performance_router
from .routers.options_admin import router as options_router
from .routers.compliance import router as compliance_router
from .routers.trading_controls import router as trading_controls_router

import time

_START_TIME = time.time()

app = FastAPI(
    title="Admin Service",
    description="Platform administration — user management, market config, fees, performance, compliance.",
    version="2.0.0",
)

app.include_router(router)
app.include_router(market_router)
app.include_router(fees_router)
app.include_router(performance_router)
app.include_router(options_router)
app.include_router(compliance_router)
app.include_router(trading_controls_router)


@app.get("/health", tags=["Health"])
async def health_check():
    from .database import engine
    from .redis_client import get_redis

    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    redis_ok = False
    try:
        redis_ok = bool(await get_redis().ping())
    except Exception:
        pass

    # Report trading halt status
    halt_active = False
    try:
        halt_active = bool(await get_redis().exists("platform:trading_halted"))
    except Exception:
        pass

    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "service": "admin-service",
        "version": "2.0.0",
        "uptime_seconds": int(time.time() - _START_TIME),
        "trading_halted": halt_active,
        "dependencies": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    }


