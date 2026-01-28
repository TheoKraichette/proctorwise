from abc import ABC, abstractmethod
from typing import List, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class Detection:
    label: str  # "face", "phone", "book", "person", etc.
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2


class MLDetector(ABC):
    @abstractmethod
    def detect_faces(self, frame: np.ndarray) -> List[Detection]:
        """Detect faces in the frame."""
        pass

    @abstractmethod
    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        """Detect forbidden objects (phones, books, etc.) in the frame."""
        pass

    @abstractmethod
    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        """Detect persons in the frame for multiple people detection."""
        pass
