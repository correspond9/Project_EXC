from contextlib import asynccontextmanager

from fastapi import FastAPI

from .redis_client import close_redis_pool, get_redis_pool
from .routers import auth, kyc, partner, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Redis connection pool on startup
    await get_redis_pool()
    yield
    # Gracefully close Redis pool on shutdown
    await close_redis_pool()


app = FastAPI(
    title="User Service",
    description=(
        "Handles user registration, login, JWT authentication, "
        "refresh token lifecycle, user profiles, and KYC status."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix="/api")
app.include_router(kyc.router, prefix="/api")
app.include_router(partner.router, prefix="/api")
app.include_router(users.router, prefix="/api")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "user-service"}
