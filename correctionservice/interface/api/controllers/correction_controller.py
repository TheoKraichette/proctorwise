import os
from typing import List

from fastapi import APIRouter, HTTPException

from application.use_cases.submit_exam import SubmitExam
from application.use_cases.auto_grade_mcq import AutoGradeMCQ
from application.use_cases.manual_grade_essay import ManualGradeAnswer, GetSubmissionResult
from infrastructure.repositories.sqlalchemy_submission_repository import SQLAlchemySubmissionRepository
from infrastructure.events.kafka_publisher import KafkaEventPublisher
from interface.api.schemas.correction_request import SubmitExamRequest, ManualGradeRequest
from interface.api.schemas.correction_response import (
    SubmissionResponse,
    GradingResultResponse,
    QuestionResultResponse,
    AnswerResponse,
    SubmissionDetailResponse
)

router = APIRouter(prefix="/corrections", tags=["Corrections"])

repo = SQLAlchemySubmissionRepository()
kafka_publisher = KafkaEventPublisher(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
)


@router.post("/submissions", response_model=SubmissionResponse)
async def submit_exam(request: SubmitExamRequest):
    use_case = SubmitExam(repo, kafka_publisher)

    answers_data = [
        {
            "question_id": a.question_id,
            "question_type": a.question_type,
            "user_answer": a.user_answer,
            "correct_answer": a.correct_answer,
            "max_score": a.max_score
        }
        for a in request.answers
    ]

    submission = await use_case.execute(
        request.user_id,
        request.exam_id,
        request.reservation_id,
        answers_data
    )

    return SubmissionResponse(
        submission_id=submission.submission_id,
        user_id=submission.user_id,
        exam_id=submission.exam_id,
        reservation_id=submission.reservation_id,
        submitted_at=submission.submitted_at,
        status=submission.status,
        total_score=submission.total_score,
        max_score=submission.max_score,
        percentage=submission.percentage,
        graded_at=submission.graded_at,
        graded_by=submission.graded_by
    )


@router.post("/submissions/{submission_id}/grade", response_model=GradingResultResponse)
async def grade_submission(submission_id: str):
    use_case = AutoGradeMCQ(repo, kafka_publisher)

    try:
        result = await use_case.execute(submission_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return GradingResultResponse(
        submission_id=result.submission_id,
        user_id=result.user_id,
        exam_id=result.exam_id,
        total_score=result.total_score,
        max_score=result.max_score,
        percentage=result.percentage,
        graded_at=result.graded_at,
        question_results=[
            QuestionResultResponse(
                question_id=qr.question_id,
                question_type=qr.question_type,
                user_answer=qr.user_answer,
                correct_answer=qr.correct_answer,
                is_correct=qr.is_correct,
                score=qr.score,
                max_score=qr.max_score,
                feedback=qr.feedback
            )
            for qr in result.question_results
        ],
        requires_manual_review=result.requires_manual_review,
        manual_review_questions=result.manual_review_questions,
        summary=result.summary
    )


@router.put("/submissions/{submission_id}/answers/{answer_id}", response_model=AnswerResponse)
async def manual_grade_answer(submission_id: str, answer_id: str, request: ManualGradeRequest):
    use_case = ManualGradeAnswer(repo, kafka_publisher)

    try:
        answer = await use_case.execute(
            submission_id,
            answer_id,
            request.score,
            request.feedback,
            request.grader_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AnswerResponse(
        answer_id=answer.answer_id,
        submission_id=answer.submission_id,
        question_id=answer.question_id,
        question_type=answer.question_type,
        user_answer=answer.user_answer,
        correct_answer=answer.correct_answer,
        is_correct=answer.is_correct,
        score=answer.score,
        max_score=answer.max_score,
        feedback=answer.feedback,
        graded_at=answer.graded_at,
        graded_by=answer.graded_by
    )


@router.get("/submissions/{submission_id}/result", response_model=SubmissionDetailResponse)
def get_submission_result(submission_id: str):
    use_case = GetSubmissionResult(repo)

    try:
        result = use_case.execute(submission_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    submission = result["submission"]
    answers = result["answers"]
    summary = result["summary"]

    return SubmissionDetailResponse(
        submission=SubmissionResponse(
            submission_id=submission.submission_id,
            user_id=submission.user_id,
            exam_id=submission.exam_id,
            reservation_id=submission.reservation_id,
            submitted_at=submission.submitted_at,
            status=submission.status,
            total_score=submission.total_score,
            max_score=submission.max_score,
            percentage=submission.percentage,
            graded_at=submission.graded_at,
            graded_by=submission.graded_by
        ),
        answers=[
            AnswerResponse(
                answer_id=a.answer_id,
                submission_id=a.submission_id,
                question_id=a.question_id,
                question_type=a.question_type,
                user_answer=a.user_answer,
                correct_answer=a.correct_answer,
                is_correct=a.is_correct,
                score=a.score,
                max_score=a.max_score,
                feedback=a.feedback,
                graded_at=a.graded_at,
                graded_by=a.graded_by
            )
            for a in answers
        ],
        summary=summary
    )


@router.get("/submissions/user/{user_id}", response_model=List[SubmissionResponse])
def get_user_submissions(user_id: str):
    submissions = repo.get_submissions_by_user(user_id)
    return [
        SubmissionResponse(
            submission_id=s.submission_id,
            user_id=s.user_id,
            exam_id=s.exam_id,
            reservation_id=s.reservation_id,
            submitted_at=s.submitted_at,
            status=s.status,
            total_score=s.total_score,
            max_score=s.max_score,
            percentage=s.percentage,
            graded_at=s.graded_at,
            graded_by=s.graded_by
        )
        for s in submissions
    ]


@router.get("/submissions/exam/{exam_id}", response_model=List[SubmissionResponse])
def get_exam_submissions(exam_id: str):
    submissions = repo.get_submissions_by_exam(exam_id)
    return [
        SubmissionResponse(
            submission_id=s.submission_id,
            user_id=s.user_id,
            exam_id=s.exam_id,
            reservation_id=s.reservation_id,
            submitted_at=s.submitted_at,
            status=s.status,
            total_score=s.total_score,
            max_score=s.max_score,
            percentage=s.percentage,
            graded_at=s.graded_at,
            graded_by=s.graded_by
        )
        for s in submissions
    ]
