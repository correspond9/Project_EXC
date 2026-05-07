from fastapi import FastAPI

from .routers.wallet import admin_router, router


app = FastAPI(
    title="Wallet Service",
    description="Manages simulation wallet balances. Admin top-up endpoint included.",
    version="0.2.0",
)

app.include_router(router)
app.include_router(admin_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "wallet-service"}
