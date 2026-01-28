from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.exam import Exam


class ExamRepository(ABC):
    @abstractmethod
    async def create(self, exam: Exam) -> Exam:
        pass

    @abstractmethod
    async def get_by_id(self, exam_id: str) -> Optional[Exam]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Exam]:
        pass

    @abstractmethod
    async def get_by_teacher(self, teacher_id: str) -> List[Exam]:
        pass

    @abstractmethod
    async def update(self, exam: Exam) -> Exam:
        pass

    @abstractmethod
    async def delete(self, exam_id: str) -> bool:
        pass
