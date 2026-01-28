from fastapi import APIRouter, HTTPException
from typing import List
import uuid

from interface.api.schemas.question_schemas import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionWithAnswerResponse,
    BulkQuestionsRequest
)
from infrastructure.repositories.sqlalchemy_question_repository import SQLAlchemyQuestionRepository
from infrastructure.repositories.sqlalchemy_exam_repository import SQLAlchemyExamRepository
from domain.entities.question import Question

router = APIRouter(prefix="/exams/{exam_id}/questions", tags=["questions"])
question_repo = SQLAlchemyQuestionRepository()
exam_repo = SQLAlchemyExamRepository()


@router.post("/", response_model=QuestionResponse)
async def add_question(exam_id: str, request: QuestionCreateRequest):
    """Add a question to an exam (teacher only)"""
    # Check exam exists
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Get current question count for numbering
    existing_questions = await question_repo.get_by_exam(exam_id)
    question_number = len(existing_questions) + 1

    question = Question(
        question_id=str(uuid.uuid4()),
        exam_id=exam_id,
        question_number=question_number,
        question_type=request.question_type,
        question_text=request.question_text,
        option_a=request.option_a,
        option_b=request.option_b,
        option_c=request.option_c,
        option_d=request.option_d,
        correct_answer=request.correct_answer,
        points=request.points
    )

    created = await question_repo.create(question)
    return QuestionResponse(
        question_id=created.question_id,
        exam_id=created.exam_id,
        question_number=created.question_number,
        question_type=created.question_type,
        question_text=created.question_text,
        option_a=created.option_a,
        option_b=created.option_b,
        option_c=created.option_c,
        option_d=created.option_d,
        points=created.points,
        created_at=created.created_at
    )


@router.post("/bulk", response_model=List[QuestionResponse])
async def add_questions_bulk(exam_id: str, request: BulkQuestionsRequest):
    """Add multiple questions to an exam at once"""
    exam = await exam_repo.get_by_id(exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    existing_questions = await question_repo.get_by_exam(exam_id)
    start_number = len(existing_questions) + 1

    created_questions = []
    for i, q in enumerate(request.questions):
        question = Question(
            question_id=str(uuid.uuid4()),
            exam_id=exam_id,
            question_number=start_number + i,
            question_type=q.question_type,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_answer=q.correct_answer,
            points=q.points
        )
        created = await question_repo.create(question)
        created_questions.append(QuestionResponse(
            question_id=created.question_id,
            exam_id=created.exam_id,
            question_number=created.question_number,
            question_type=created.question_type,
            question_text=created.question_text,
            option_a=created.option_a,
            option_b=created.option_b,
            option_c=created.option_c,
            option_d=created.option_d,
            points=created.points,
            created_at=created.created_at
        ))

    return created_questions


@router.get("/", response_model=List[QuestionResponse])
async def get_questions(exam_id: str):
    """Get all questions for an exam (without correct answers - for students)"""
    questions = await question_repo.get_by_exam(exam_id)
    return [
        QuestionResponse(
            question_id=q.question_id,
            exam_id=q.exam_id,
            question_number=q.question_number,
            question_type=q.question_type,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            points=q.points,
            created_at=q.created_at
        )
        for q in questions
    ]


@router.get("/with-answers", response_model=List[QuestionWithAnswerResponse])
async def get_questions_with_answers(exam_id: str):
    """Get all questions with correct answers (for teachers only)"""
    questions = await question_repo.get_by_exam(exam_id)
    return [
        QuestionWithAnswerResponse(
            question_id=q.question_id,
            exam_id=q.exam_id,
            question_number=q.question_number,
            question_type=q.question_type,
            question_text=q.question_text,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
            correct_answer=q.correct_answer,
            points=q.points,
            created_at=q.created_at
        )
        for q in questions
    ]


@router.delete("/{question_id}")
async def delete_question(exam_id: str, question_id: str):
    """Delete a question"""
    success = await question_repo.delete(question_id)
    if not success:
        raise HTTPException(status_code=404, detail="Question not found")
    return {"message": "Question deleted"}
