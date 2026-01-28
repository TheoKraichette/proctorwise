from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.question import Question


class QuestionRepository(ABC):
    @abstractmethod
    async def create(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def get_by_id(self, question_id: str) -> Optional[Question]:
        pass

    @abstractmethod
    async def get_by_exam(self, exam_id: str) -> List[Question]:
        pass

    @abstractmethod
    async def update(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def delete(self, question_id: str) -> bool:
        pass

    @abstractmethod
    async def delete_by_exam(self, exam_id: str) -> bool:
        pass
