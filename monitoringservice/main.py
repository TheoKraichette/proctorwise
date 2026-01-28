from fastapi import FastAPI
from interface.api.controllers import monitoring_controller

app = FastAPI(
    title="ProctorWise Monitoring Service",
    description="Real-time exam proctoring with hybrid ML/rule-based anomaly detection",
    version="1.0.0"
)

app.include_router(monitoring_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "monitoring"}
