from fastapi import FastAPI

app = FastAPI(
    title="Notification Service",
    description="Sends email and in-app notifications: order fills, margin calls, system alerts.",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "notification-service"}
