from fastapi import FastAPI

app = FastAPI(
    title="Wallet Service",
    description="Manages simulation wallet balances, margin allocation, deposits, and withdrawals.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "wallet-service"}
