from datetime import datetime
from typing import List, Dict
import uuid

from domain.entities.exam_submission import ExamSubmission
from domain.entities.answer import Answer
from application.interfaces.submission_repository import SubmissionRepository
from application.interfaces.event_publisher import EventPublisher


class SubmitExam:
    def __init__(self, repository: SubmissionRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(
        self,
        user_id: str,
        exam_id: str,
        reservation_id: str,
        answers: List[Dict]
    ) -> ExamSubmission:
        submission_id = str(uuid.uuid4())
        now = datetime.utcnow()

        submission = ExamSubmission(
            submission_id=submission_id,
            user_id=user_id,
            exam_id=exam_id,
            reservation_id=reservation_id,
            submitted_at=now,
            status="submitted"
        )

        self.repository.create_submission(submission)

        for ans_data in answers:
            answer = Answer(
                answer_id=str(uuid.uuid4()),
                submission_id=submission_id,
                question_id=ans_data["question_id"],
                question_type=ans_data["question_type"],
                user_answer=ans_data["user_answer"],
                correct_answer=ans_data.get("correct_answer"),
                max_score=ans_data.get("max_score", 1.0)
            )
            self.repository.create_answer(answer)

        await self.event_publisher.publish("exam_submitted", {
            "submission_id": submission_id,
            "user_id": user_id,
            "exam_id": exam_id,
            "reservation_id": reservation_id,
            "submitted_at": now.isoformat(),
            "answer_count": len(answers)
        })

        return submission
