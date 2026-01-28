from fastapi import FastAPI
from interface.api.controllers import correction_controller

app = FastAPI(
    title="ProctorWise Correction Service",
    description="Exam submission and grading service with auto-grading for MCQ and manual review for essays",
    version="1.0.0"
)

app.include_router(correction_controller.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "correction"}
