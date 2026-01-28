from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExamCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    duration_minutes: int = 60
    teacher_id: str


class ExamUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_minutes: Optional[int] = None


class ExamResponse(BaseModel):
    exam_id: str
    title: str
    description: Optional[str]
    duration_minutes: int
    teacher_id: str
    status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
