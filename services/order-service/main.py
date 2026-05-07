from fastapi import FastAPI

app = FastAPI(
    title="Order Service",
    description="Handles order creation, validation, and routing to the simulation or live execution engine.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "order-service"}
