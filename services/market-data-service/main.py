from fastapi import FastAPI

app = FastAPI(
    title="Market Data Service",
    description="Connects to Binance WebSocket for live prices, OHLCV storage, and real-time price broadcast.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "market-data-service"}
