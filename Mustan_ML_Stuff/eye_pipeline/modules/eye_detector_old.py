"""
Eye Movement Detection Module - 2-Stage Pipeline
Stage 1: MediaPipe finds and crops eyes from face
Stage 2: YOLOv8-pose analyzes cropped eyes for keypoints and risk assessment

This solves the scale mismatch problem where the model was trained on cropped eyes
but receives full webcam frames.
"""

import logging
import cv2
import numpy as np
import mediapipe as mp


class EyeMovementDetector:
    """Detects eyes using 2-stage pipeline: MediaPipe + YOLOv8-pose for risk assessment"""
    
    def __init__(self, model_path='best.pt', confidence_threshold=0.25):
        """
        Initialize Eye Movement Detector with 2-stage pipeline
        
        Args:
            model_path: Path to best.pt YOLOv8-pose model
            confidence_threshold: Minimum confidence for YOLO predictions
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        
        # MediaPipe Face Mesh (Stage 1: Eye Locator)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # Critical for accurate eye outlines
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # MediaPipe eye landmark indices
        # Left Eye (user's left): [33, 133, 159, 145]
        # Right Eye (user's right): [362, 263, 386, 374]
        self.eyes_indices = [
            {'name': 'Left', 'indices': [33, 133, 159, 145]},
            {'name': 'Right', 'indices': [362, 263, 386, 374]}
        ]
        
        # Risk analysis thresholds (from notebook)
        self.vertical_threshold = 0.15
        self.horizontal_min = 0.3
        self.horizontal_max = 0.7
        
        # Keypoint colors
        self.keypoint_colors = {
            'inner': (0, 255, 255),   # Yellow (caruncle)
            'outer': (255, 0, 255),   # Magenta (interior margin)
            'pupil': (0, 255, 0)      # Green (pupil center)
        }
        
        # Risk status colors
        self.risk_colors = {
            'SAFE': (0, 255, 0),      # Green
            'RISK': (0, 0, 255),      # Red
            'THINKING': (255, 165, 0) # Orange
        }
        
        logging.info(f"Initializing 2-Stage Eye Detector: MediaPipe + YOLO")
        logging.info(f"Model: {model_path}")
        
    def load_models(self):
        """Load the YOLOv8 keypoint detection model"""
        try:
            from ultralytics import YOLO
            
            self.model = YOLO(self.model_path)
            logging.info(f"Eye detection model loaded: {self.model_path}")
            
            # Check if model has keypoints
            if hasattr(self.model, 'names'):
                logging.info(f"Model classes: {self.model.names}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading eye detection model: {e}")
            return False
    
    def detect_eyes_with_keypoints(self, frame):
        """
        Detect eyes and extract keypoints
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            list: List of eye detections with keypoints
                  Each detection: {
                      'bbox': (cx, cy, w, h),
                      'confidence': float,
                      'keypoints': {
                          'inner': (x, y, vis),
                          'outer': (x, y, vis),
                          'pupil': (x, y, vis)
                      }
                  }
        """
        if self.model is None:
            logging.warning("Model not loaded")
            return []
        
        try:
            # Run inference with lower confidence for debugging
            results = self.model(frame, verbose=False, conf=self.confidence_threshold)
            
            detections = []
            
            for result in results:
                # Get bounding boxes
                boxes = result.boxes
                
                # Debug: Log what we're detecting
                if len(boxes) > 0:
                    logging.info(f"Detected {len(boxes)} objects")
                    for idx, box in enumerate(boxes):
                        conf = float(box.conf[0])
                        logging.info(f"  Object {idx}: confidence={conf:.3f}")
                else:
                    logging.debug("No objects detected in frame")
                
                # Check if keypoints are available
                if hasattr(result, 'keypoints') and result.keypoints is not None:
                    keypoints = result.keypoints
                    logging.info(f"Keypoints available: {len(keypoints.xy)} sets")
                    
                    for i, box in enumerate(boxes):
                        # Extract bounding box
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        w = x2 - x1
                        h = y2 - y1
                        confidence = float(box.conf[0])
                        
                        # Extract keypoints (3 keypoints per eye)
                        if i < len(keypoints.xy):
                            kpts = keypoints.xy[i].cpu().numpy()  # Shape: (3, 2)
                            kpts_conf = keypoints.conf[i].cpu().numpy() if hasattr(keypoints, 'conf') else np.ones(3)
                            
                            if len(kpts) >= 3:
                                detection = {
                                    'bbox': (int(cx), int(cy), int(w), int(h)),
                                    'xyxy': (int(x1), int(y1), int(x2), int(y2)),
                                    'confidence': confidence,
                                    'keypoints': {
                                        'inner': (float(kpts[0][0]), float(kpts[0][1]), float(kpts_conf[0])),
                                        'outer': (float(kpts[1][0]), float(kpts[1][1]), float(kpts_conf[1])),
                                        'pupil': (float(kpts[2][0]), float(kpts[2][1]), float(kpts_conf[2]))
                                    }
                                }
                                detections.append(detection)
                else:
                    # No keypoints, just use bounding box
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        cx = (x1 + x2) / 2
                        cy = (y1 + y2) / 2
                        w = x2 - x1
                        h = y2 - y1
                        confidence = float(box.conf[0])
                        
                        detections.append({
                            'bbox': (int(cx), int(cy), int(w), int(h)),
                            'xyxy': (int(x1), int(y1), int(x2), int(y2)),
                            'confidence': confidence,
                            'keypoints': None
                        })
            
            return detections
            
        except Exception as e:
            logging.error(f"Error during eye detection: {e}")
            return []
    
    def calculate_risk(self, keypoints):
        """
        Calculate risk status based on pupil position (from notebook)
        
        Args:
            keypoints: Dictionary with 'inner', 'outer', 'pupil' positions
                      Format: {'inner': (x, y, vis), 'outer': (x, y, vis), 'pupil': (x, y, vis)}
            
        Returns:
            tuple: (status, score, horizontal_ratio, vertical_ratio)
                   status: "LOOKING DOWN (RISK)", "LOOKING UP (THINKING)", 
                          "LOOKING SIDE (RISK)", "CENTER (SAFE)"
                   score: The dominant ratio value
        """
        if keypoints is None:
            return "Error", 0.0, 0.0, 0.0
        
        try:
            # Extract keypoint coordinates
            inner_x, inner_y, inner_vis = keypoints['inner']
            outer_x, outer_y, outer_vis = keypoints['outer']
            pupil_x, pupil_y, pupil_vis = keypoints['pupil']
            
            # Check if keypoints are visible
            if inner_vis < 0.3 or outer_vis < 0.3 or pupil_vis < 0.3:
                return "EYE CLOSED", 0.0, 0.0, 0.0
            
            # 1. Calculate Eye Width
            eye_width = abs(outer_x - inner_x) + 1e-6  # Avoid div/0
            
            # 2. Vertical Ratio (Pupil Y vs Eye Center Y)
            eye_center_y = (inner_y + outer_y) / 2
            vertical_ratio = (pupil_y - eye_center_y) / eye_width
            
            # 3. Horizontal Ratio
            horizontal_ratio = (pupil_x - inner_x) / eye_width
            
            # 4. Determine Status
            # Positive V-Ratio = Looking Down (Y increases downwards)
            if vertical_ratio > self.vertical_threshold:
                return "LOOKING DOWN (RISK)", vertical_ratio, horizontal_ratio, vertical_ratio
            elif vertical_ratio < -self.vertical_threshold:
                return "LOOKING UP (THINKING)", abs(vertical_ratio), horizontal_ratio, vertical_ratio
            elif horizontal_ratio < self.horizontal_min or horizontal_ratio > self.horizontal_max:
                return "LOOKING SIDE (RISK)", abs(horizontal_ratio - 0.5) * 2, horizontal_ratio, vertical_ratio
            else:
                return "CENTER (SAFE)", 1.0 - abs(vertical_ratio), horizontal_ratio, vertical_ratio
        
        except Exception as e:
            logging.error(f"Error in risk calculation: {e}")
            return "Error", 0.0, 0.0, 0.0
    
    def draw_eye_detection(self, frame, detection, draw_keypoints=True, 
                          box_color=(255, 0, 0), thickness=2):
        """
        Draw eye detection with bounding box and keypoints
        
        Args:
            frame: Input frame
            detection: Detection dictionary
            draw_keypoints: Whether to draw keypoints
            box_color: Color for bounding box
            thickness: Line thickness
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw bounding box
        x1, y1, x2, y2 = detection['xyxy']
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, thickness)
        
        # Draw confidence
        confidence = detection['confidence']
        cv2.putText(annotated_frame, f"{confidence:.2f}", 
                   (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, box_color, 2)
        
        # Draw keypoints if available
        if draw_keypoints and detection['keypoints'] is not None:
            keypoints = detection['keypoints']
            
            # Draw lines connecting keypoints (eye outline)
            inner_pt = (int(keypoints['inner'][0]), int(keypoints['inner'][1]))
            outer_pt = (int(keypoints['outer'][0]), int(keypoints['outer'][1]))
            pupil_pt = (int(keypoints['pupil'][0]), int(keypoints['pupil'][1]))
            
            # Draw line between corners
            if keypoints['inner'][2] > 0.3 and keypoints['outer'][2] > 0.3:
                cv2.line(annotated_frame, inner_pt, outer_pt, (255, 255, 255), 1)
            
            # Draw keypoints
            if keypoints['inner'][2] > 0.3:
                cv2.circle(annotated_frame, inner_pt, 3, self.keypoint_colors['inner'], -1)
                cv2.putText(annotated_frame, "I", 
                           (inner_pt[0] - 10, inner_pt[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.keypoint_colors['inner'], 1)
            
            if keypoints['outer'][2] > 0.3:
                cv2.circle(annotated_frame, outer_pt, 3, self.keypoint_colors['outer'], -1)
                cv2.putText(annotated_frame, "O", 
                           (outer_pt[0] + 10, outer_pt[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.keypoint_colors['outer'], 1)
            
            if keypoints['pupil'][2] > 0.3:
                cv2.circle(annotated_frame, pupil_pt, 4, self.keypoint_colors['pupil'], -1)
                cv2.putText(annotated_frame, "P", 
                           (pupil_pt[0], pupil_pt[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, self.keypoint_colors['pupil'], 1)
        
        return annotated_frame
    
    def process_frame(self, frame, draw=True, color=(255, 0, 0), thickness=2):
        """
        Detect eyes and classify eye movements in frame
        
        Args:
            frame: Input frame
            draw: Whether to draw results
            color: Color for bounding boxes
            thickness: Line thickness
            
        Returns:
            tuple: (processed_frame, detections_with_classification)
        """
        processed_frame = frame.copy()
        
        # Detect eyes with keypoints
        detections = self.detect_eyes_with_keypoints(frame)
        
        # Analyze risk for each detection
        risk_detections = []
        
        for detection in detections:
            # Calculate risk status
            status, score, h_ratio, v_ratio = self.calculate_risk(
                detection['keypoints']
            )
            
            # Add risk analysis to detection
            detection['risk_status'] = status
            detection['risk_score'] = score
            detection['horizontal_ratio'] = h_ratio
            detection['vertical_ratio'] = v_ratio
            
            risk_detections.append(detection)
            
            # Draw detection
            if draw:
                # Determine color based on risk
                if "RISK" in status:
                    box_color = self.risk_colors['RISK']
                elif "THINKING" in status:
                    box_color = self.risk_colors['THINKING']
                elif "SAFE" in status:
                    box_color = self.risk_colors['SAFE']
                else:
                    box_color = color
                
                processed_frame = self.draw_eye_detection(
                    processed_frame, detection, 
                    draw_keypoints=True,
                    box_color=box_color,
                    thickness=thickness
                )
                
                # Draw risk status label
                x1, y1, x2, y2 = detection['xyxy']
                label = f"{status}"
                score_label = f"Score: {score:.2f}"
                
                # Background for label
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                cv2.rectangle(processed_frame,
                            (x1, y2),
                            (x1 + label_size[0] + 10, y2 + 30),
                            box_color, -1)
                
                # Status text
                cv2.putText(processed_frame, label,
                           (x1 + 5, y2 + 15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                           (255, 255, 255), 2)
                
                # Score text
                cv2.putText(processed_frame, score_label,
                           (x1 + 5, y2 + 28),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                           (255, 255, 255), 1)
        
        return processed_frame, risk_detections
