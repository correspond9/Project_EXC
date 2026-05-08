from fastapi import FastAPI

from .routers.wallet import admin_router, router
from .routers.real_wallet import router as real_wallet_router
from .routers.real_wallet import admin_router as real_wallet_admin_router


app = FastAPI(
    title="Wallet Service",
    description="Manages simulation and real wallet balances.",
    version="0.3.0",
)

app.include_router(router)
app.include_router(admin_router)
app.include_router(real_wallet_router)
app.include_router(real_wallet_admin_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "wallet-service"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "wallet-service"}
