import time

from fastapi import FastAPI

from .routers.options import router as options_router
from .routers.orders import router

_START_TIME = time.time()

app = FastAPI(
    title="Order Service",
    description="Accepts order submissions, tracks order lifecycle, routes to execution engine.",
    version="2.0.0",
)

app.include_router(router)
app.include_router(options_router)


@app.get("/health", tags=["Health"])
async def health_check():
    from .database import engine
    from .redis_client import get_redis_pool

    # Quick DB ping
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy", fromlist=["text"]).text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # Quick Redis ping
    redis_ok = False
    try:
        redis_ok = await get_redis_pool().ping()
    except Exception:
        pass

    uptime_s = int(time.time() - _START_TIME)
    return {
        "status": "ok" if (db_ok and redis_ok) else "degraded",
        "service": "order-service",
        "version": "2.0.0",
        "uptime_seconds": uptime_s,
        "dependencies": {"database": "ok" if db_ok else "error", "redis": "ok" if redis_ok else "error"},
    }
