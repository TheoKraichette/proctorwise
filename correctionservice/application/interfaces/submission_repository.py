from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.exam_submission import ExamSubmission
from domain.entities.answer import Answer


class SubmissionRepository(ABC):
    @abstractmethod
    def create_submission(self, submission: ExamSubmission) -> None:
        pass

    @abstractmethod
    def get_submission_by_id(self, submission_id: str) -> Optional[ExamSubmission]:
        pass

    @abstractmethod
    def get_submissions_by_user(self, user_id: str) -> List[ExamSubmission]:
        pass

    @abstractmethod
    def get_submissions_by_exam(self, exam_id: str) -> List[ExamSubmission]:
        pass

    @abstractmethod
    def update_submission(self, submission: ExamSubmission) -> None:
        pass

    @abstractmethod
    def create_answer(self, answer: Answer) -> None:
        pass

    @abstractmethod
    def get_answers_by_submission(self, submission_id: str) -> List[Answer]:
        pass

    @abstractmethod
    def get_answer_by_id(self, answer_id: str) -> Optional[Answer]:
        pass

    @abstractmethod
    def update_answer(self, answer: Answer) -> None:
        pass
