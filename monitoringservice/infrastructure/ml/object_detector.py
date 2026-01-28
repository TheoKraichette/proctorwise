from typing import List
import numpy as np

from application.interfaces.ml_detector import MLDetector, Detection


class YOLOObjectDetector(MLDetector):
    FORBIDDEN_CLASSES = {
        67: "cell phone",
        73: "book",
        63: "laptop",
        0: "person"
    }

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.5):
        self.model = None
        self.model_path = model_path or "yolov8n.pt"
        self.confidence_threshold = confidence_threshold
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
            self.model = None

    def detect_faces(self, frame: np.ndarray) -> List[Detection]:
        return []

    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        if self.model is None:
            return []

        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if conf < self.confidence_threshold:
                    continue

                if cls in self.FORBIDDEN_CLASSES and cls != 0:
                    xyxy = box.xyxy[0].cpu().numpy()
                    detections.append(Detection(
                        label=self.FORBIDDEN_CLASSES[cls],
                        confidence=conf,
                        bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
                    ))

        return detections

    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        if self.model is None:
            return []

        results = self.model(frame, verbose=False)
        detections = []

        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if cls == 0 and conf >= self.confidence_threshold:
                    xyxy = box.xyxy[0].cpu().numpy()
                    detections.append(Detection(
                        label="person",
                        confidence=conf,
                        bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
                    ))

        return detections


class HybridDetector(MLDetector):
    def __init__(
        self,
        face_detector: MLDetector = None,
        object_detector: MLDetector = None
    ):
        from .face_detector import MediaPipeFaceDetector
        self.face_detector = face_detector or MediaPipeFaceDetector()
        self.object_detector = object_detector or YOLOObjectDetector()

    def detect_faces(self, frame: np.ndarray) -> List[Detection]:
        return self.face_detector.detect_faces(frame)

    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        return self.object_detector.detect_objects(frame)

    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        return self.object_detector.detect_persons(frame)
