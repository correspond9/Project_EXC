from fastapi import FastAPI

from .routers.orders import router


app = FastAPI(
    title="Order Service",
    description="Accepts order submissions, tracks order lifecycle, routes to execution engine.",
    version="0.2.0",
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "order-service"}
