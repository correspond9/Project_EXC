from fastapi import FastAPI

app = FastAPI(
    title="Admin Service",
    description=(
        "ADMIN and SUPER_ADMIN panel APIs: user management, platform config, "
        "simulation reset, fee settings, and TOTP-protected super admin actions."
    ),
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "admin-service"}
