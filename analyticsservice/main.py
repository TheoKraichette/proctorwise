from fastapi import FastAPI
from interface.api.controllers import analytics_controller

app = FastAPI(
    title="ProctorWise Analytics Service",
    description="Analytics and reporting service for exam performance and platform metrics",
    version="1.0.0"
)

app.include_router(analytics_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "analytics"}
