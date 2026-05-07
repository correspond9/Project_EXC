from fastapi import FastAPI

app = FastAPI(
    title="User Service",
    description="Handles registration, login, JWT authentication, user profiles, and KYC.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "user-service"}
