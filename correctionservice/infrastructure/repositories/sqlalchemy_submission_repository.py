from typing import List, Optional

from infrastructure.database.models import ExamSubmissionModel, AnswerModel
from infrastructure.database.mariadb_cluster import SessionLocal
from domain.entities.exam_submission import ExamSubmission
from domain.entities.answer import Answer
from application.interfaces.submission_repository import SubmissionRepository


class SQLAlchemySubmissionRepository(SubmissionRepository):

    def create_submission(self, submission: ExamSubmission) -> None:
        session = SessionLocal()
        db_submission = ExamSubmissionModel(
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
        session.add(db_submission)
        session.commit()
        session.close()

    def get_submission_by_id(self, submission_id: str) -> Optional[ExamSubmission]:
        session = SessionLocal()
        result = session.query(ExamSubmissionModel).filter_by(submission_id=submission_id).first()
        session.close()
        if not result:
            return None
        return ExamSubmission(
            submission_id=result.submission_id,
            user_id=result.user_id,
            exam_id=result.exam_id,
            reservation_id=result.reservation_id,
            submitted_at=result.submitted_at,
            status=result.status,
            total_score=result.total_score,
            max_score=result.max_score,
            percentage=result.percentage,
            graded_at=result.graded_at,
            graded_by=result.graded_by
        )

    def get_submissions_by_user(self, user_id: str) -> List[ExamSubmission]:
        session = SessionLocal()
        results = session.query(ExamSubmissionModel).filter_by(user_id=user_id).all()
        session.close()
        return [
            ExamSubmission(
                submission_id=r.submission_id,
                user_id=r.user_id,
                exam_id=r.exam_id,
                reservation_id=r.reservation_id,
                submitted_at=r.submitted_at,
                status=r.status,
                total_score=r.total_score,
                max_score=r.max_score,
                percentage=r.percentage,
                graded_at=r.graded_at,
                graded_by=r.graded_by
            )
            for r in results
        ]

    def get_submissions_by_exam(self, exam_id: str) -> List[ExamSubmission]:
        session = SessionLocal()
        results = session.query(ExamSubmissionModel).filter_by(exam_id=exam_id).all()
        session.close()
        return [
            ExamSubmission(
                submission_id=r.submission_id,
                user_id=r.user_id,
                exam_id=r.exam_id,
                reservation_id=r.reservation_id,
                submitted_at=r.submitted_at,
                status=r.status,
                total_score=r.total_score,
                max_score=r.max_score,
                percentage=r.percentage,
                graded_at=r.graded_at,
                graded_by=r.graded_by
            )
            for r in results
        ]

    def update_submission(self, submission: ExamSubmission) -> None:
        session = SessionLocal()
        db_submission = session.query(ExamSubmissionModel).filter_by(
            submission_id=submission.submission_id
        ).first()
        if db_submission:
            db_submission.status = submission.status
            db_submission.total_score = submission.total_score
            db_submission.max_score = submission.max_score
            db_submission.percentage = submission.percentage
            db_submission.graded_at = submission.graded_at
            db_submission.graded_by = submission.graded_by
            session.commit()
        session.close()

    def create_answer(self, answer: Answer) -> None:
        session = SessionLocal()
        db_answer = AnswerModel(
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
        session.add(db_answer)
        session.commit()
        session.close()

    def get_answers_by_submission(self, submission_id: str) -> List[Answer]:
        session = SessionLocal()
        results = session.query(AnswerModel).filter_by(submission_id=submission_id).all()
        session.close()
        return [
            Answer(
                answer_id=r.answer_id,
                submission_id=r.submission_id,
                question_id=r.question_id,
                question_type=r.question_type,
                user_answer=r.user_answer,
                correct_answer=r.correct_answer,
                is_correct=r.is_correct,
                score=r.score,
                max_score=r.max_score,
                feedback=r.feedback,
                graded_at=r.graded_at,
                graded_by=r.graded_by
            )
            for r in results
        ]

    def get_answer_by_id(self, answer_id: str) -> Optional[Answer]:
        session = SessionLocal()
        result = session.query(AnswerModel).filter_by(answer_id=answer_id).first()
        session.close()
        if not result:
            return None
        return Answer(
            answer_id=result.answer_id,
            submission_id=result.submission_id,
            question_id=result.question_id,
            question_type=result.question_type,
            user_answer=result.user_answer,
            correct_answer=result.correct_answer,
            is_correct=result.is_correct,
            score=result.score,
            max_score=result.max_score,
            feedback=result.feedback,
            graded_at=result.graded_at,
            graded_by=result.graded_by
        )

    def update_answer(self, answer: Answer) -> None:
        session = SessionLocal()
        db_answer = session.query(AnswerModel).filter_by(answer_id=answer.answer_id).first()
        if db_answer:
            db_answer.is_correct = answer.is_correct
            db_answer.score = answer.score
            db_answer.feedback = answer.feedback
            db_answer.graded_at = answer.graded_at
            db_answer.graded_by = answer.graded_by
            session.commit()
        session.close()
