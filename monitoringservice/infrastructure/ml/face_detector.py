from typing import List
import numpy as np

from application.interfaces.ml_detector import MLDetector, Detection

class YOLOFaceDetector(MLDetector):
    def __init__(self, model_path: str = None):
        self.model = None
        self.model_path = model_path or "yolov8n-face.pt"
        self._load_model()

    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
        except Exception as e:
            print(f"Warning: Could not load YOLO model: {e}")
            self.model = None

    def detect_faces(self, frame: np.ndarray) -> List[Detection]:
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
                xyxy = box.xyxy[0].cpu().numpy()
                detections.append(Detection(
                    label="face",
                    confidence=conf,
                    bbox=(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
                ))

        return detections

    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        return []

    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        return []


class MediaPipeFaceDetector(MLDetector):
    def __init__(self, min_detection_confidence: float = 0.5):
        self.min_detection_confidence = min_detection_confidence
        self.face_detection = None
        self._load_model()

    def _load_model(self):
        try:
            import mediapipe as mp
            self.face_detection = mp.solutions.face_detection.FaceDetection(
                min_detection_confidence=self.min_detection_confidence
            )
        except Exception as e:
            print(f"Warning: Could not load MediaPipe model: {e}")
            self.face_detection = None

    def detect_faces(self, frame: np.ndarray) -> List[Detection]:
        if self.face_detection is None:
            return []

        import cv2
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(rgb_frame)

        detections = []
        if results.detections:
            h, w, _ = frame.shape
            for detection in results.detections:
                bbox = detection.location_data.relative_bounding_box
                x1 = int(bbox.xmin * w)
                y1 = int(bbox.ymin * h)
                x2 = int((bbox.xmin + bbox.width) * w)
                y2 = int((bbox.ymin + bbox.height) * h)

                detections.append(Detection(
                    label="face",
                    confidence=detection.score[0],
                    bbox=(x1, y1, x2, y2)
                ))

        return detections

    def detect_objects(self, frame: np.ndarray) -> List[Detection]:
        return []

    def detect_persons(self, frame: np.ndarray) -> List[Detection]:
        return []
