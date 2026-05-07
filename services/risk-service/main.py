from fastapi import FastAPI

app = FastAPI(
    title="Risk Service",
    description="Pre-trade and post-trade risk checks: margin validation, position limits, liquidation triggers.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "risk-service"}
