from datetime import datetime
from typing import List

from domain.entities.exam_submission import ExamSubmission
from domain.entities.answer import Answer
from domain.entities.grading_result import GradingResult, QuestionResult
from application.interfaces.submission_repository import SubmissionRepository
from application.interfaces.event_publisher import EventPublisher


class AutoGradeMCQ:
    AUTO_GRADABLE_TYPES = ["mcq", "true_false", "short_answer"]

    def __init__(self, repository: SubmissionRepository, event_publisher: EventPublisher):
        self.repository = repository
        self.event_publisher = event_publisher

    async def execute(self, submission_id: str) -> GradingResult:
        submission = self.repository.get_submission_by_id(submission_id)
        if not submission:
            raise ValueError(f"Submission {submission_id} not found")

        if submission.status not in ["submitted", "grading"]:
            raise ValueError(f"Submission {submission_id} cannot be graded (status: {submission.status})")

        submission.status = "grading"
        self.repository.update_submission(submission)

        answers = self.repository.get_answers_by_submission(submission_id)
        now = datetime.utcnow()

        question_results = []
        total_score = 0.0
        max_score = 0.0
        manual_review_questions = []

        for answer in answers:
            max_score += answer.max_score

            if answer.question_type in self.AUTO_GRADABLE_TYPES:
                graded_answer = self._grade_answer(answer)
                graded_answer.graded_at = now
                graded_answer.graded_by = "auto"
                self.repository.update_answer(graded_answer)
                total_score += graded_answer.score or 0

                question_results.append(QuestionResult(
                    question_id=answer.question_id,
                    question_type=answer.question_type,
                    user_answer=answer.user_answer,
                    correct_answer=answer.correct_answer,
                    is_correct=graded_answer.is_correct,
                    score=graded_answer.score or 0,
                    max_score=answer.max_score,
                    feedback=graded_answer.feedback
                ))
            else:
                manual_review_questions.append(answer.question_id)
                question_results.append(QuestionResult(
                    question_id=answer.question_id,
                    question_type=answer.question_type,
                    user_answer=answer.user_answer,
                    correct_answer=None,
                    is_correct=None,
                    score=0,
                    max_score=answer.max_score,
                    feedback="Requires manual review"
                ))

        requires_manual_review = len(manual_review_questions) > 0
        percentage = (total_score / max_score * 100) if max_score > 0 else 0

        submission.total_score = total_score
        submission.max_score = max_score
        submission.percentage = percentage
        submission.graded_at = now
        submission.graded_by = "auto" if not requires_manual_review else None
        submission.status = "manual_review" if requires_manual_review else "graded"
        self.repository.update_submission(submission)

        summary = {
            "correct": sum(1 for qr in question_results if qr.is_correct is True),
            "incorrect": sum(1 for qr in question_results if qr.is_correct is False),
            "pending": sum(1 for qr in question_results if qr.is_correct is None)
        }

        grading_result = GradingResult(
            submission_id=submission_id,
            user_id=submission.user_id,
            exam_id=submission.exam_id,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            graded_at=now,
            question_results=question_results,
            requires_manual_review=requires_manual_review,
            manual_review_questions=manual_review_questions,
            summary=summary
        )

        if requires_manual_review:
            await self.event_publisher.publish("manual_review_required", {
                "submission_id": submission_id,
                "user_id": submission.user_id,
                "exam_id": submission.exam_id,
                "questions_requiring_review": manual_review_questions,
                "partial_score": total_score,
                "max_score": max_score
            })
        else:
            await self.event_publisher.publish("grading_completed", {
                "submission_id": submission_id,
                "user_id": submission.user_id,
                "exam_id": submission.exam_id,
                "total_score": total_score,
                "max_score": max_score,
                "percentage": percentage,
                "graded_at": now.isoformat()
            })

        return grading_result

    def _grade_answer(self, answer: Answer) -> Answer:
        if answer.correct_answer is None:
            answer.is_correct = None
            answer.score = 0
            answer.feedback = "No correct answer provided for auto-grading"
            return answer

        user_answer = answer.user_answer.strip().lower()
        correct_answer = answer.correct_answer.strip().lower()

        if answer.question_type == "mcq":
            answer.is_correct = user_answer == correct_answer
            answer.score = answer.max_score if answer.is_correct else 0
            answer.feedback = "Correct!" if answer.is_correct else f"Incorrect. The correct answer was: {answer.correct_answer}"

        elif answer.question_type == "true_false":
            answer.is_correct = user_answer == correct_answer
            answer.score = answer.max_score if answer.is_correct else 0
            answer.feedback = "Correct!" if answer.is_correct else f"Incorrect. The answer was: {answer.correct_answer}"

        elif answer.question_type == "short_answer":
            answer.is_correct = self._fuzzy_match(user_answer, correct_answer)
            answer.score = answer.max_score if answer.is_correct else 0
            answer.feedback = "Correct!" if answer.is_correct else "Incorrect."

        return answer

    def _fuzzy_match(self, user_answer: str, correct_answer: str, threshold: float = 0.85) -> bool:
        if user_answer == correct_answer:
            return True

        correct_words = set(correct_answer.split())
        user_words = set(user_answer.split())

        if not correct_words:
            return False

        intersection = correct_words.intersection(user_words)
        similarity = len(intersection) / len(correct_words)

        return similarity >= threshold
