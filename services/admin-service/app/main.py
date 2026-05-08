from fastapi import FastAPI

from .routers.admin import router
from .routers.market import router as market_router
from .routers.fees import router as fees_router
from .routers.performance import router as performance_router
from .routers.options_admin import router as options_router


app = FastAPI(
    title="Admin Service",
    description="Platform administration — user management, market config, fees, performance.",
    version="0.3.0",
)

app.include_router(router)
app.include_router(market_router)
app.include_router(fees_router)
app.include_router(performance_router)
app.include_router(options_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "admin-service"}

