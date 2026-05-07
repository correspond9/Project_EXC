from fastapi import FastAPI

app = FastAPI(
    title="Portfolio Service",
    description="Tracks positions, P&L, unrealised gains, and portfolio snapshots for each user.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "portfolio-service"}
