from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from interface.api.controllers import correction_controller
from infrastructure.database.mariadb_cluster import engine
from infrastructure.database.models import Base

app = FastAPI(
    title="ProctorWise Correction Service",
    description="Exam submission and grading service with auto-grading for MCQ and manual review for essays",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(correction_controller.router)


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "correction"}
