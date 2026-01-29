import os
from typing import Optional
from datetime import datetime
import numpy as np
import cv2
import io

from application.interfaces.frame_storage import FrameStorage


class HDFSFrameStorage(FrameStorage):
    def __init__(self, hdfs_url: str = None, base_path: str = "/proctorwise/raw/frames"):
        self.hdfs_url = hdfs_url or os.getenv("HDFS_URL", "http://namenode:9870")
        self.base_path = base_path
        self.client = None
        self._connect()

    def _connect(self):
        try:
            from hdfs import InsecureClient
            self.client = InsecureClient(self.hdfs_url)
        except Exception as e:
            print(f"Warning: Could not connect to HDFS: {e}")
            self.client = None

    def _get_frame_path(self, session_id: str, frame_number: int) -> str:
        now = datetime.utcnow()
        return f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}/frame_{frame_number:06d}.jpg"

    def store_frame(self, session_id: str, frame_number: int, frame: np.ndarray) -> str:
        path = self._get_frame_path(session_id, frame_number)

        _, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_bytes = encoded.tobytes()

        if self.client:
            try:
                dir_path = os.path.dirname(path)
                self.client.makedirs(dir_path)
                with self.client.write(path, overwrite=True) as writer:
                    writer.write(frame_bytes)
            except Exception as e:
                print(f"Warning: Could not write to HDFS: {e}")

        return path

    def get_frame(self, path: str) -> Optional[np.ndarray]:
        if not self.client:
            return None

        try:
            with self.client.read(path) as reader:
                frame_bytes = reader.read()
                nparr = np.frombuffer(frame_bytes, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                return frame
        except Exception as e:
            print(f"Warning: Could not read from HDFS: {e}")
            return None

    def delete_session_frames(self, session_id: str) -> None:
        if not self.client:
            return

        try:
            now = datetime.utcnow()
            session_path = f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}"
            self.client.delete(session_path, recursive=True)
        except Exception as e:
            print(f"Warning: Could not delete from HDFS: {e}")

    def get_frame_count(self, session_id: str) -> int:
        if not self.client:
            return 0

        try:
            now = datetime.utcnow()
            session_path = f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}"
            files = self.client.list(session_path)
            return len([f for f in files if f.endswith('.jpg')])
        except Exception:
            return 0


class LocalFrameStorage(FrameStorage):
    def __init__(self, base_path: str = "./local_storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_frame_path(self, session_id: str, frame_number: int) -> str:
        now = datetime.utcnow()
        return f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}/frame_{frame_number:06d}.jpg"

    def store_frame(self, session_id: str, frame_number: int, frame: np.ndarray) -> str:
        path = self._get_frame_path(session_id, frame_number)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        cv2.imwrite(path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return path

    def get_frame(self, path: str) -> Optional[np.ndarray]:
        if not os.path.exists(path):
            return None
        return cv2.imread(path)

    def delete_session_frames(self, session_id: str) -> None:
        import shutil
        now = datetime.utcnow()
        session_path = f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}"
        if os.path.exists(session_path):
            shutil.rmtree(session_path)

    def get_frame_count(self, session_id: str) -> int:
        now = datetime.utcnow()
        session_path = f"{self.base_path}/{now.year}/{now.month:02d}/{now.day:02d}/{session_id}"
        if not os.path.exists(session_path):
            return 0
        return len([f for f in os.listdir(session_path) if f.endswith('.jpg')])
