# ===========================================================
# EXECUTION SERVICE — Phase 4+ (Live Trading)
# ===========================================================
# This service is a PLACEHOLDER for Sprint 1.
# It will NOT be built or started unless Docker Compose is
# run with --profile live (see docker-compose.yml).
#
# In Phase 4, this service will:
#   - Connect to Binance via CCXT
#   - Route live orders to Binance Spot and Futures
#   - Report fills back to the order-service
#   - Support both Binance Spot and USD-M Futures
# ===========================================================

from fastapi import FastAPI

app = FastAPI(
    title="Execution Service (Phase 4+)",
    description=(
        "Routes real orders to Binance via CCXT. "
        "Only active in LIVE mode (--profile live). "
        "Disabled in SIMULATION mode."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "execution-service", "mode": "placeholder"}
