"""
Face Detection Module
Handles face detection using YOLOv8
"""

import logging
import cv2
import numpy as np


class YOLOv8Detector:
    """Object detection using YOLOv8"""
    
    def __init__(self, model_name='yolov8n.pt', confidence_threshold=0.5):
        """
        Initialize YOLOv8 object detector
        
        Args:
            model_name: Name of the YOLOv8 model (e.g., 'yolov8n.pt')
            confidence_threshold: Minimum confidence for detection
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        logging.info(f"Initializing YOLOv8 detector with model: {model_name}")
        
    def load_model(self):
        """Load the YOLOv8 model"""
        try:
            from ultralytics import YOLO
            
            # Load YOLOv8 model
            self.model = YOLO(self.model_name)
            logging.info(f"YOLOv8 model '{self.model_name}' loaded successfully")
            return True
            
        except ImportError:
            logging.error("ultralytics package not installed. Install with: pip install ultralytics")
            return False
        except Exception as e:
            logging.error(f"Error loading YOLOv8 model: {e}")
            return False
    
    def detect_objects(self, frame, target_classes=None):
        """
        Detect objects in a frame
        
        Args:
            frame: Input frame (BGR format)
            target_classes: List of class IDs to detect (e.g., [0] for 'person')
            
        Returns:
            list: List of bounding boxes [(x1, y1, x2, y2, confidence, class_id), ...]
        """
        if self.model is None:
            logging.warning("Model not loaded")
            return []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False, conf=self.confidence_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    
                    # Filter by target classes if specified
                    if target_classes is not None and class_id not in target_classes:
                        continue
                    
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = float(box.conf[0])
                    
                    detections.append((int(x1), int(y1), int(x2), int(y2), confidence, class_id))
            
            return detections
            
        except Exception as e:
            logging.error(f"Error during object detection: {e}")
            return []
    
    def draw_boxes(self, frame, detections, color=(0, 255, 0), thickness=2, show_confidence=True):
        """
        Draw bounding boxes around detected objects
        
        Args:
            frame: Input frame
            detections: List of bounding boxes
            color: Color for bounding box (B, G, R)
            thickness: Line thickness
            show_confidence: Whether to display confidence scores
            
        Returns:
            Frame with drawn bounding boxes
        """
        output_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2, confidence, class_id = detection
            
            # Draw rectangle
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label
            if show_confidence:
                label = f"{self.model.names[class_id]}: {confidence:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                
                # Background for text
                cv2.rectangle(
                    output_frame,
                    (x1, y1 - label_size[1] - 10),
                    (x1 + label_size[0], y1),
                    color,
                    -1
                )
                
                # Text
                cv2.putText(
                    output_frame,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return output_frame
    
    def process_frame(self, frame, target_classes=None, draw=True, color=(0, 255, 0), thickness=2):
        """
        Detect objects and optionally draw bounding boxes
        
        Args:
            frame: Input frame
            target_classes: List of class IDs to detect
            draw: Whether to draw bounding boxes
            color: Color for bounding box
            thickness: Line thickness
            
        Returns:
            tuple: (processed_frame, detections)
        """
        detections = self.detect_objects(frame, target_classes)
        
        if draw:
            output_frame = self.draw_boxes(frame, detections, color, thickness)
        else:
            output_frame = frame
        
        return output_frame, detections



class HaarCascadeFaceDetector:
    """Face detection using OpenCV Haar Cascades (fallback option)"""
    
    def __init__(self, scale_factor=1.1, min_neighbors=5):
        """
        Initialize Haar Cascade face detector
        
        Args:
            scale_factor: Parameter specifying how much the image size is reduced
            min_neighbors: Parameter specifying how many neighbors each candidate rectangle should have
        """
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.cascade = None
        
        logging.info("Initializing Haar Cascade face detector")
    
    def load_model(self):
        """Load Haar Cascade classifier"""
        try:
            self.cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            logging.info("Haar Cascade face detector loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Error loading Haar Cascade: {e}")
            return False
    
    def detect_faces(self, frame):
        """Detect faces using Haar Cascade"""
        if self.cascade is None:
            logging.warning("Cascade not loaded")
            return []
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces_rect = self.cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors
        )
        
        # Convert to same format as YOLO: (x1, y1, x2, y2, confidence)
        faces = []
        for (x, y, w, h) in faces_rect:
            faces.append((x, y, x + w, y + h, 1.0))
        
        return faces
    
    def draw_faces(self, frame, faces, color=(0, 255, 0), thickness=2, show_confidence=False):
        """Draw bounding boxes around detected faces"""
        output_frame = frame.copy()
        
        for face in faces:
            x1, y1, x2, y2, _ = face
            cv2.rectangle(output_frame, (x1, y1), (x2, y2), color, thickness)
        
        return output_frame
    
    def process_frame(self, frame, draw=True, color=(0, 255, 0), thickness=2):
        """Detect faces and optionally draw bounding boxes"""
        faces = self.detect_faces(frame)
        
        if draw:
            output_frame = self.draw_faces(frame, faces, color, thickness)
        else:
            output_frame = frame
        
        return output_frame, faces
