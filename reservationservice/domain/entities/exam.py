from dataclasses import dataclass

@dataclass
class Exam:
    exam_id: str
    title: str
    description: str
    duration_minutes: int
