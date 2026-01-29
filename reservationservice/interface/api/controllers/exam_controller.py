from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from interface.api.schemas.exam_schemas import ExamCreateRequest, ExamUpdateRequest, ExamResponse, ExamSlotCreateRequest, ExamSlotResponse
from infrastructure.repositories.sqlalchemy_exam_repository import SQLAlchemyExamRepository
from domain.entities.exam import Exam

router = APIRouter(prefix="/exams", tags=["exams"])
exam_repo = SQLAlchemyExamRepository()


@router.post("/", response_model=ExamResponse)
async def create_exam(request: ExamCreateRequest):
    """Create a new exam (for teachers)"""
    exam = Exam(
        exam_id=str(uuid.uuid4()),
        title=request.title,
        description=request.description,
        duration_minutes=request.duration_minutes,
        teacher_id=request.teacher_id,
        status="active"
    )
    created_exam = await exam_repo.create(exam)
    return ExamResponse(
        exam_id=created_exam.exam_id,
        title=created_exam.title,
        description=created_exam.description,
        duration_minutes=created_exam.duration_minutes,
        teacher_id=created_exam.teacher_id,
        status=created_exam.status,
        created_at=created_exam.created_at
    )


@router.get("/", response_model=List[ExamResponse])
async def list_all_exams():
    """List all active exams"""
    exams = await exam_repo.get_all()
    return [
        ExamResponse(
            exam_id=e.exam_id,
            title=e.title,
            description=e.description,
            duration_minutes=e.duration_minutes,
            teacher_id=e.teacher_id,
            status=e.status,
            created_at=e.created_at
        )
        for e in exams
    ]


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(exam_id: str):
    """Get exam by ID"""
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return ExamResponse(
        exam_id=exam.exam_id,
        title=exam.title,
        description=exam.description,
        duration_minutes=exam.duration_minutes,
        teacher_id=exam.teacher_id,
        status=exam.status,
        created_at=exam.created_at
    )


@router.get("/teacher/{teacher_id}", response_model=List[ExamResponse])
async def list_exams_by_teacher(teacher_id: str):
    """List all exams created by a teacher"""
    exams = await exam_repo.get_by_teacher(teacher_id)
    return [
        ExamResponse(
            exam_id=e.exam_id,
            title=e.title,
            description=e.description,
            duration_minutes=e.duration_minutes,
            teacher_id=e.teacher_id,
            status=e.status,
            created_at=e.created_at
        )
        for e in exams
    ]


@router.put("/{exam_id}", response_model=ExamResponse)
async def update_exam(exam_id: str, request: ExamUpdateRequest):
    """Update an exam"""
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    if request.title:
        exam.title = request.title
    if request.description is not None:
        exam.description = request.description
    if request.duration_minutes:
        exam.duration_minutes = request.duration_minutes

    updated_exam = await exam_repo.update(exam)
    return ExamResponse(
        exam_id=updated_exam.exam_id,
        title=updated_exam.title,
        description=updated_exam.description,
        duration_minutes=updated_exam.duration_minutes,
        teacher_id=updated_exam.teacher_id,
        status=updated_exam.status,
        created_at=updated_exam.created_at
    )


@router.delete("/{exam_id}")
async def delete_exam(exam_id: str):
    """Delete an exam (soft delete)"""
    success = await exam_repo.delete(exam_id)
    if not success:
        raise HTTPException(status_code=404, detail="Exam not found")
    return {"message": "Exam deleted successfully"}


# ========== EXAM SLOTS ==========

@router.post("/{exam_id}/slots", response_model=ExamSlotResponse)
async def create_slot(exam_id: str, request: ExamSlotCreateRequest):
    """Add a time slot to an exam"""
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    slot = await exam_repo.create_slot(exam_id, request.start_time)
    return ExamSlotResponse(
        slot_id=slot.slot_id,
        exam_id=slot.exam_id,
        start_time=slot.start_time,
        created_at=slot.created_at
    )


@router.get("/{exam_id}/slots", response_model=List[ExamSlotResponse])
async def list_slots(exam_id: str):
    """List all time slots for an exam"""
    slots = await exam_repo.get_slots_by_exam(exam_id)
    return [
        ExamSlotResponse(
            slot_id=s.slot_id,
            exam_id=s.exam_id,
            start_time=s.start_time,
            created_at=s.created_at
        )
        for s in slots
    ]


@router.delete("/{exam_id}/slots/{slot_id}")
async def delete_slot(exam_id: str, slot_id: str):
    """Remove a time slot from an exam"""
    success = await exam_repo.delete_slot(slot_id)
    if not success:
        raise HTTPException(status_code=404, detail="Slot not found")
    return {"message": "Slot deleted successfully"}
