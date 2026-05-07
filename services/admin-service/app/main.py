from fastapi import FastAPI

from .routers.admin import router


app = FastAPI(
    title="Admin Service",
    description="Platform administration — user management, mode switching, account control.",
    version="0.2.0",
)

app.include_router(router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "admin-service"}
