from fastapi import FastAPI

app = FastAPI(
    title="Simulation Engine",
    description=(
        "Executes simulated order fills against real Binance prices. "
        "Mimics live execution logic without touching real funds. "
        "Active from Phase 1; remains available in Phase 4+ as a parallel mode."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "simulation-engine"}
