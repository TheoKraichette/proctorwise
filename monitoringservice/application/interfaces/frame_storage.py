from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class FrameStorage(ABC):
    @abstractmethod
    def store_frame(self, session_id: str, frame_number: int, frame: np.ndarray) -> str:
        """Store a frame and return its storage path."""
        pass

    @abstractmethod
    def get_frame(self, path: str) -> Optional[np.ndarray]:
        """Retrieve a frame by its storage path."""
        pass

    @abstractmethod
    def delete_session_frames(self, session_id: str) -> None:
        """Delete all frames for a session."""
        pass

    @abstractmethod
    def get_frame_count(self, session_id: str) -> int:
        """Get the number of stored frames for a session."""
        pass
