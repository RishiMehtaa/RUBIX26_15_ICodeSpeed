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
        """Load the YOLOv8 keypoint detection model (Stage 2)"""
        try:
            from ultralytics import YOLO
            
            self.model = YOLO(self.model_path)
            logging.info(f"✓ YOLO model loaded: {self.model_path}")
            logging.info(f"✓ MediaPipe Face Mesh initialized")
            
            # Check if model has keypoints
            if hasattr(self.model, 'names'):
                logging.info(f"Model classes: {self.model.names}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading eye detection model: {e}")
            return False
    
    def detect_eyes_with_keypoints(self, frame):
        """
        2-Stage Detection Pipeline:
        Stage 1: MediaPipe finds eyes in full frame
        Stage 2: YOLO analyzes cropped eyes for keypoints
        
        Args:
            frame: Input frame (BGR)
            
        Returns:
            list: List of eye detections with keypoints and crop info
        """
        if self.model is None:
            logging.warning("Model not loaded")
            return []
        
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # STAGE 1: MediaPipe finds the face and eye regions
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            logging.debug("No face detected by MediaPipe")
            return []
        
        detections = []
        
        # Extract eye regions from MediaPipe landmarks
        mesh_points = np.array([
            np.multiply([p.x, p.y], [w, h]).astype(int) 
            for p in results.multi_face_landmarks[0].landmark
        ])
        
        for eye_info in self.eyes_indices:
            try:
                # Get bounding box of the eye from MediaPipe
                pts = mesh_points[eye_info['indices']]
                min_x, min_y = np.min(pts, axis=0)
                max_x, max_y = np.max(pts, axis=0)
                
                # Add padding (make it square and slightly larger like training data)
                eye_w, eye_h = max_x - min_x, max_y - min_y
                center_x, center_y = min_x + eye_w//2, min_y + eye_h//2
                
                # Crop size: 1.8x the width (to include eyebrows/corners)
                crop_size = int(max(eye_w, eye_h) * 1.8)
                
                # Coordinates for cropping
                x1 = max(0, center_x - crop_size)
                y1 = max(0, center_y - crop_size)
                x2 = min(w, center_x + crop_size)
                y2 = min(h, center_y + crop_size)
                
                # STAGE 2: Crop the eye region
                eye_crop = frame[y1:y2, x1:x2]
                if eye_crop.size == 0:
                    continue
                
                # STAGE 3: Run YOLO on the cropped eye (matches training data scale)
                yolo_results = self.model(eye_crop, verbose=False, conf=self.confidence_threshold)
                
                for r in yolo_results:
                    # Check if keypoints are available
                    if hasattr(r, 'keypoints') and r.keypoints is not None and len(r.keypoints.xy) > 0:
                        kpts = r.keypoints.xy[0].cpu().numpy()  # Keypoints relative to crop
                        kpts_conf = r.keypoints.conf[0].cpu().numpy() if hasattr(r.keypoints, 'conf') else np.ones(3)
                        
                        # Get bounding box from YOLO (relative to crop)
                        if len(r.boxes) > 0:
                            box = r.boxes[0]
                            confidence = float(box.conf[0])
                            
                            # Store detection with crop info for drawing on full frame
                            detection = {
                                'eye_name': eye_info['name'],
                                'crop_region': (x1, y1, x2, y2),
                                'bbox': (int(x1), int(y1), int(x2), int(y2)),  # Full frame coordinates
                                'xyxy': (int(x1), int(y1), int(x2), int(y2)),
                                'confidence': confidence,
                                'keypoints': {
                                    'inner': (float(kpts[0][0]), float(kpts[0][1]), float(kpts_conf[0])),
                                    'outer': (float(kpts[1][0]), float(kpts[1][1]), float(kpts_conf[1])),
                                    'pupil': (float(kpts[2][0]), float(kpts[2][1]), float(kpts_conf[2]))
                                },
                                'keypoints_crop_relative': kpts  # For drawing
                            }
                            detections.append(detection)
                            logging.debug(f"{eye_info['name']} eye detected with keypoints")
            
            except Exception as e:
                logging.debug(f"Error processing {eye_info['name']} eye: {e}")
                continue
        
        logging.debug(f"Total eyes detected: {len(detections)}") 
        return detections
    
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
            detection: Detection dictionary with crop_region info
            draw_keypoints: Whether to draw keypoints
            box_color: Color for bounding box
            thickness: Line thickness
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        # Draw bounding box (crop region)
        x1, y1, x2, y2 = detection['crop_region']
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), box_color, thickness)
        
        # Draw confidence
        confidence = detection['confidence']
        cv2.putText(annotated_frame, f"{confidence:.2f}", 
                   (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, box_color, 2)
        
        # Draw keypoints if available (map from crop coordinates to full frame)
        if draw_keypoints and detection['keypoints'] is not None:
            kpts_crop = detection['keypoints_crop_relative']
            
            # Map keypoints from crop coordinates to full frame
            for idx, (name, color) in enumerate([('inner', self.keypoint_colors['inner']),
                                                   ('outer', self.keypoint_colors['outer']),
                                                   ('pupil', self.keypoint_colors['pupil'])]):
                if idx < len(kpts_crop):
                    kx, ky = kpts_crop[idx]
                    # Map to full frame coordinates
                    full_x = int(x1 + kx)
                    full_y = int(y1 + ky)
                    
                    cv2.circle(annotated_frame, (full_x, full_y), 4, color, -1)
                    
                    # Draw line between inner and outer corners
                    if idx == 1 and 0 < len(kpts_crop):  # outer corner
                        inner_x = int(x1 + kpts_crop[0][0])
                        inner_y = int(y1 + kpts_crop[0][1])
                        cv2.line(annotated_frame, (inner_x, inner_y), (full_x, full_y), (255, 255, 255), 1)
        
        return annotated_frame
    
    def process_frame(self, frame, draw=True, color=(255, 0, 0), thickness=2):
        """
        Detect eyes and calculate risk in frame using 2-stage pipeline
        
        Args:
            frame: Input frame
            draw: Whether to draw results
            color: Color for bounding boxes
            thickness: Line thickness
            
        Returns:
            tuple: (processed_frame, detections_with_risk)
        """
        processed_frame = frame.copy()
        
        # Detect eyes with keypoints using 2-stage pipeline
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
                x1, y1, x2, y2 = detection['crop_region']
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
