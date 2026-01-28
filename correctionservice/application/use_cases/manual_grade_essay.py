from datetime import datetime
from typing import Optional

from domain.entities.exam_submission import ExamSubmission
from domain.entities.answer import Answer
from application.interfaces.submission_repository import SubmissionRepository
from application.interfaces.event_publisher import EventPublisher


class ManualGradeAnswer:
    def __init__(self, repository: SubmissionRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(
        self,
        submission_id: str,
        answer_id: str,
        score: float,
        feedback: Optional[str],
        grader_id: str
    ) -> Answer:
        submission = self.repository.get_submission_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        answer = self.repository.get_answer_by_id(answer_id)
        if not answer:
            raise ValueError(f"Answer {answer_id} not found")

        if answer.submission_id != submission_id:
            raise ValueError(f"Answer {answer_id} does not belong to submission {submission_id}")

        if score < 0 or score > answer.max_score:
            raise ValueError(f"Score must be between 0 and {answer.max_score}")

        now = datetime.utcnow()
        answer.score = score
        answer.is_correct = score >= answer.max_score * 0.5
        answer.feedback = feedback
        answer.graded_at = now
        answer.graded_by = grader_id

        self.repository.update_answer(answer)

        await self._recalculate_submission_score(submission)

        return answer

    async def _recalculate_submission_score(self, submission: ExamSubmission):
        answers = self.repository.get_answers_by_submission(submission.submission_id)

        all_graded = all(a.graded_at is not None for a in answers)
        total_score = sum(a.score or 0 for a in answers)
        max_score = sum(a.max_score for a in answers)
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        submission.total_score = total_score
        submission.max_score = max_score
        submission.percentage = percentage

        if all_graded:
            submission.status = "graded"
            submission.graded_at = datetime.utcnow()
            submission.graded_by = "mixed"  # Both auto and manual grading

            await self.event_publisher.publish("grading_completed", {
                "submission_id": submission.submission_id,
                "user_id": submission.user_id,
                "exam_id": submission.exam_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": percentage,
                "graded_at": submission.graded_at.isoformat()
            })

        self.repository.update_submission(submission)


class GetSubmissionResult:
    def __init__(self, repository: SubmissionRepository):
        self.repository = repository

    def execute(self, submission_id: str) -> dict:
        submission = self.repository.get_submission_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        answers = self.repository.get_answers_by_submission(submission_id)

        return {
            "submission": submission,
            "answers": answers,
            "summary": {
                "total_questions": len(answers),
                "graded": sum(1 for a in answers if a.graded_at is not None),
                "pending": sum(1 for a in answers if a.graded_at is None),
                "correct": sum(1 for a in answers if a.is_correct is True),
                "incorrect": sum(1 for a in answers if a.is_correct is False)
            }
        }
