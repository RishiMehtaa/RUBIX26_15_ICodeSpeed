"""
Proctor Module
Main proctoring pipeline that orchestrates multiple detection modules
"""

import logging
import cv2
import time
from .camera_pipeline import CameraPipeline
from .base_detector import BaseDetector
from .proctor_logger import ProctorLogger


class ProctorPipeline(CameraPipeline):
    """
    Proctoring pipeline that inherits from CameraPipeline.
    Manages multiple detector modules and processes frames at a configurable rate.
    """
    
    def __init__(self, config=None, frame_skip=2, session_id=None):
        """
        Initialize proctoring pipeline
        
        Args:
            config: Configuration object (uses default Config if None)
            frame_skip: Number of frames to skip between processing (default: 2, process every 3rd frame)
            session_id: Optional session ID for logging
        """
        super().__init__(config)
        
        # Detector management
        self.detectors = {}  # Changed to dict for easier lookup
        self.face_detector = None
        self.face_matcher = None
        self.eye_detector = None  # Add eye detector reference
        self.frame_skip = frame_skip
        self.frame_counter = 0
        
        # Session logger
        self.session_logger = ProctorLogger(session_id=session_id)
        
        # Proctoring state
        self.proctoring_results = {
            "total_frames_captured": 0,
            "total_frames_processed": 0,
            "detections": {},
            "alerts": []
        }
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info(f"Proctoring pipeline initialized with frame_skip={frame_skip}, sequential processing enabled")
        self.session_logger.log_info(f"Proctoring pipeline initialized with frame_skip={frame_skip}")
    
    def register_detector(self, detector: BaseDetector):
        """
        Register a detector module to the proctoring pipeline
        
        Args:
            detector: An instance of BaseDetector or its subclass
            
        Returns:
            bool: True if detector was registered successfully
        """
        if not isinstance(detector, BaseDetector):
            self.logger.error(f"Detector must be an instance of BaseDetector, got {type(detector)}")
            return False
        
        # Initialize detector if not already initialized
        if not detector.initialized:
            self.logger.info(f"Initializing detector: {detector.name}")
            if not detector.load_model():
                self.logger.error(f"Failed to initialize detector: {detector.name}")
                return False
        
        # Store detector
        self.detectors[detector.name] = detector
        
        # Keep references to specific detectors for optimized pipeline
        # Check in order of specificity to avoid false matches
        if detector.name == "FaceDetector":
            self.face_detector = detector
        elif detector.name == "FaceMatcher":
            self.face_matcher = detector
        elif detector.name == "EyeDetector" or "Eye" in detector.name:
            self.eye_detector = detector
        elif "Detector" in detector.name and "Face" in detector.name:
            # Fallback for face detectors with different names
            self.face_detector = detector
        elif "Matcher" in detector.name or "Match" in detector.name:
            # Fallback for matchers with different names
            self.face_matcher = detector
        
        self.proctoring_results["detections"][detector.name] = []
        self.logger.info(f"Registered detector: {detector.name}")
        self.session_logger.log_info(f"Registered detector: {detector.name}")
        return True
    
    def unregister_detector(self, detector_name: str):
        """
        Unregister a detector module by name
        
        Args:
            detector_name: Name of the detector to remove
            
        Returns:
            bool: True if detector was removed
        """
        if detector_name in self.detectors:
            del self.detectors[detector_name]
            self.logger.info(f"Unregistered detector: {detector_name}")
            self.session_logger.log_info(f"Unregistered detector: {detector_name}")
            return True
        
        self.logger.warning(f"Detector not found: {detector_name}")
        return False
    
    def get_detector(self, detector_name: str):
        """
        Get a detector by name
        
        Args:
            detector_name: Name of the detector
            
        Returns:
            BaseDetector or None: The detector instance if found
        """
        return self.detectors.get(detector_name)
    
    def list_detectors(self):
        """
        Get list of all registered detectors
        
        Returns:
            list: List of detector names and their status
        """
        return [
            {
                "name": name,
                "enabled": detector.enabled,
                "initialized": detector.initialized
            }
            for name, detector in self.detectors.items()
        ]
    
    def enable_detector(self, detector_name: str):
        """Enable a detector by name"""
        detector = self.get_detector(detector_name)
        if detector:
            detector.enable()
            return True
        return False
    
    def disable_detector(self, detector_name: str):
        """Disable a detector by name"""
        detector = self.get_detector(detector_name)
        if detector:
            detector.disable()
            return True
        return False
    

    
    def process_frame(self, frame):
        """
        Process frame with SEQUENTIAL pipeline:
        1. MediaPipe face detector gets faces
        2. Multiple faces alert
        3. If single face then verify
        4. After verify check eye movement
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processed frame with annotations
        """
        self.proctoring_results["total_frames_captured"] += 1
        self.frame_counter += 1
        
        # Check if we should process this frame
        if self.frame_counter <= self.frame_skip:
            # Skip processing, just return the frame with basic overlay
            return self._add_skip_overlay(frame)
        
        # Reset counter
        self.frame_counter = 0
        self.proctoring_results["total_frames_processed"] += 1
        self.session_logger.log_frame_processed()
        
        annotated_frame = frame.copy()
        
        # STEP 1: MediaPipe face detector gets faces
        face_meshes = []
        if self.face_detector and self.face_detector.enabled:
            try:
                face_meshes = self.face_detector.detect(frame)
            except Exception as e:
                self.logger.error(f"Error detecting faces: {e}")
                self.session_logger.log_alert('detection_error', f"Face detection failed: {e}", 'critical')
        
        num_faces = len(face_meshes)
        verification_result = None
        eye_result = None
        
        # STEP 2: Multiple faces alert
        if num_faces > 1:
            # Multiple faces detected - LOG ALERT
            alert_msg = f"Multiple people detected: {num_faces} faces"
            self.logger.warning(alert_msg)
            self.session_logger.log_alert(
                'multiple_faces',
                alert_msg,
                'warning',
                {'num_faces': num_faces}
            )
            self.proctoring_results["alerts"].append({
                "timestamp": time.time(),
                "type": "multiple_faces",
                "message": alert_msg,
                "severity": "warning"
            })
        elif num_faces == 0:
            # No face detected - LOG ALERT
            alert_msg = "No face detected"
            self.logger.warning(alert_msg)
            self.session_logger.log_alert(
                'no_face',
                alert_msg,
                'warning'
            )
            self.proctoring_results["alerts"].append({
                "timestamp": time.time(),
                "type": "no_face",
                "message": alert_msg,
                "severity": "warning"
            })
        elif num_faces == 1:
            # STEP 3: If single face then verify
            if self.face_matcher and self.face_matcher.enabled:
                try:
                    verification_result = self._verify_face_sequential(frame, face_meshes[0])
                except Exception as e:
                    self.logger.error(f"Error during face verification: {e}")
                    self.session_logger.log_alert('verification_error', f"Verification failed: {e}", 'critical')
                    verification_result = {'matched': False, 'error': str(e)}
            
            # STEP 4: After verify check eye movement
            if self.eye_detector and self.eye_detector.enabled:
                try:
                    eye_result = self.eye_detector.detect_eyes_with_keypoints(frame, face_meshes)
                    
                    # Check for eye movement alerts
                    if eye_result and 'eyes' in eye_result:
                        for eye_data in eye_result['eyes']:
                            if eye_data.get('risk_status') == 'RISK':
                                alert_msg = f"Suspicious eye movement detected: {eye_data.get('name', 'Unknown')} eye"
                                self.logger.warning(alert_msg)
                                self.session_logger.log_alert(
                                    'eye_movement',
                                    alert_msg,
                                    'warning',
                                    eye_data
                                )
                                self.proctoring_results["alerts"].append({
                                    "timestamp": time.time(),
                                    "type": "eye_movement",
                                    "message": alert_msg,
                                    "severity": "warning"
                                })
                except Exception as e:
                    self.logger.error(f"Error during eye detection: {e}")
                    self.session_logger.log_alert('eye_detection_error', f"Eye detection failed: {e}", 'info')
        
        # Draw face meshes on frame
        if face_meshes and self.face_detector:
            annotated_frame = self.face_detector.draw_faces(annotated_frame, face_meshes)
        
        # Draw eye detection results if available
        if eye_result and self.eye_detector:
            try:
                annotated_frame = self.eye_detector.draw_eye_keypoints(annotated_frame, eye_result)
            except Exception as e:
                self.logger.error(f"Error drawing eye keypoints: {e}")
        
        # Add verification status overlay (top left)
        annotated_frame = self._add_verification_overlay(annotated_frame, num_faces, verification_result, eye_result)
        
        return annotated_frame
    
    def _verify_face_sequential(self, frame, face_data):
        """
        Sequential face verification (no threading)
        
        Args:
            frame: Input frame
            face_data: Face mesh data
            
        Returns:
            dict: Verification result
        """
        try:
            bbox = face_data['bbox']
            x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
            
            # Extract face ROI
            face_roi = frame[y:y+h, x:x+w]
            
            # Match face
            result = self.face_matcher.match_with_details(face_roi)
            
            # Log result
            if result.get('matched'):
                self.session_logger.log_info(f"Face verified - confidence: {result.get('confidence', 0):.2f}")
            else:
                self.session_logger.log_alert(
                    'face_mismatch',
                    f"Face verification failed - distance: {result.get('distance', 'N/A')}",
                    'warning',
                    result
                )
            
            return result
        except Exception as e:
            self.logger.error(f"Error in face verification: {e}")
            return {'matched': False, 'error': str(e)}
    
    def _add_skip_overlay(self, frame):
        """Add overlay for skipped frames"""
        overlay = frame.copy()
        cv2.putText(
            overlay,
            f"Frame {self.proctoring_results['total_frames_captured']} (skipped)",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1
        )
        return overlay
    
    def _add_verification_overlay(self, frame, num_faces, verification_result, eye_result=None):
        """
        Add verification status overlay to top left
        
        Args:
            frame: Input frame
            num_faces: Number of faces detected
            verification_result: Verification result from FaceMatcher
            eye_result: Eye detection result (optional)
            
        Returns:
            Frame with overlay
        """
        overlay = frame.copy()
        
        # Determine status text and color
        if num_faces > 1:
            status_text = f"ALERT: {num_faces} PEOPLE DETECTED"
            color = (0, 0, 255)  # Red
        elif num_faces == 0:
            status_text = "NO FACE DETECTED"
            color = (0, 0, 255)  # Red
        elif verification_result:
            if verification_result.get('matched'):
                status_text = "VERIFIED"
                color = (0, 255, 0)  # Green
                confidence = verification_result.get('confidence', 0)
                status_text += f" ({confidence:.1%})"
            else:
                status_text = "UNVERIFIED"
                color = (0, 165, 255)  # Orange
        else:
            status_text = "CHECKING..."
            color = (255, 255, 0)  # Yellow
        
        # Draw background rectangle
        text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.rectangle(overlay, (5, 5), (text_size[0] + 15, 40), (0, 0, 0), -1)
        
        # Draw status text
        cv2.putText(
            overlay,
            status_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )
        
        # Add eye status if available
        if eye_result and 'eyes' in eye_result:
            y_offset = 50
            for eye_data in eye_result['eyes']:
                eye_status = eye_data.get('risk_status', 'UNKNOWN')
                eye_color = (0, 255, 0) if eye_status == 'SAFE' else (0, 0, 255) if eye_status == 'RISK' else (255, 165, 0)
                eye_text = f"{eye_data.get('name', 'Eye')}: {eye_status}"
                cv2.putText(
                    overlay,
                    eye_text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    eye_color,
                    1
                )
                y_offset += 20
        
        # Add frame counter
        stats_text = f"Frame: {self.proctoring_results['total_frames_processed']}/{self.proctoring_results['total_frames_captured']}"
        cv2.putText(
            overlay,
            stats_text,
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        return overlay
    
    def _draw_all_detections(self, frame, frame_detections):
        """
        Draw all detection results on the frame
        
        Args:
            frame: Input frame
            frame_detections: Dictionary of detection results from all detectors
            
        Returns:
            Frame with all annotations drawn
        """
        annotated_frame = frame.copy()
        
        # Draw each detector's results
        for detector_name, results in frame_detections.items():
            detector = self.get_detector(detector_name)
            if not detector:
                continue
            
            try:
                # For face detector, draw faces with verification info
                if detector_name == "FaceDetector" and results.get("num_faces", 0) > 0:
                    face_objs = results.get("faces", [])
                    verification = results.get("verification")
                    
                    # Call detector's draw method
                    annotated_frame = detector.draw_faces(
                        annotated_frame,
                        face_objs,
                        verification_result=verification
                    )
                
                # For other detectors, check if they have detection results
                elif hasattr(detector, 'draw_detections') and results.get("detections"):
                    detections = results.get("detections", [])
                    annotated_frame = detector.draw_detections(annotated_frame, detections)
                    
            except Exception as e:
                self.logger.error(f"Error drawing detections for {detector_name}: {e}")
        
        return annotated_frame
    
    def _check_alerts(self, detector_name: str, detection_results: dict):
        """
        Check detection results for alert conditions
        Can be customized based on proctoring rules
        
        Args:
            detector_name: Name of the detector
            detection_results: Results from the detector
        """
        # Example: Alert if multiple faces detected
        if detector_name == "FaceDetector":
            num_faces = detection_results.get("num_faces", 0)
            
            if num_faces > 1:
                alert = {
                    "timestamp": time.time(),
                    "detector": detector_name,
                    "type": "multiple_faces",
                    "message": f"Multiple faces detected: {num_faces}",
                    "severity": "warning"
                }
                self.proctoring_results["alerts"].append(alert)
                self.logger.warning(f"ALERT: {alert['message']}")
            elif num_faces == 0:
                alert = {
                    "timestamp": time.time(),
                    "detector": detector_name,
                    "type": "no_face",
                    "message": "No face detected",
                    "severity": "warning"
                }
                self.proctoring_results["alerts"].append(alert)
                self.logger.warning(f"ALERT: {alert['message']}")
    
    def _add_proctoring_overlay(self, frame, frame_detections):
        """
        Add proctoring information overlay to frame
        
        Args:
            frame: Input frame
            frame_detections: Detection results for current frame
            
        Returns:
            Frame with overlay
        """
        overlay_frame = frame.copy()
        
        # Add detector status
        y_offset = 60
        for detector_name, results in frame_detections.items():
            status_text = f"{detector_name}: "
            
            if detector_name == "FaceDetector":
                num_faces = results.get("num_faces", 0)
                # Handle verification safely - it might be None
                verification = results.get("verification") or {}
                verified = verification.get("verified", False)
                
                if verified:
                    status_text += f"Verified ({num_faces} faces)"
                    color = (0, 255, 0)  # Green
                elif num_faces > 0:
                    status_text += f"Unverified ({num_faces} faces)"
                    color = (0, 165, 255)  # Orange
                else:
                    status_text += "No face detected"
                    color = (0, 0, 255)  # Red
            else:
                status_text += "Active"
                color = (255, 255, 255)  # White
            
            cv2.putText(
                overlay_frame,
                status_text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )
            y_offset += 25
        
        # Add frame processing stats
        stats_text = f"Processed: {self.proctoring_results['total_frames_processed']}/{self.proctoring_results['total_frames_captured']}"
        cv2.putText(
            overlay_frame,
            stats_text,
            (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
        
        return overlay_frame
    
    def get_proctoring_report(self):
        """
        Generate a comprehensive proctoring report
        
        Returns:
            dict: Proctoring statistics and results
        """
        report = {
            "session_stats": {
                "total_frames_captured": self.proctoring_results["total_frames_captured"],
                "total_frames_processed": self.proctoring_results["total_frames_processed"],
                "frame_skip": self.frame_skip,
                "processing_ratio": (
                    self.proctoring_results["total_frames_processed"] / 
                    self.proctoring_results["total_frames_captured"]
                    if self.proctoring_results["total_frames_captured"] > 0 else 0
                )
            },
            "detectors": self.list_detectors(),
            "alerts": self.proctoring_results["alerts"],
            "alert_summary": self._get_alert_summary()
        }
        
        return report
    
    def _get_alert_summary(self):
        """Generate summary of alerts"""
        summary = {}
        for alert in self.proctoring_results["alerts"]:
            alert_type = alert.get("type", "unknown")
            if alert_type not in summary:
                summary[alert_type] = 0
            summary[alert_type] += 1
        return summary
    
    def start(self):
        """
        Start the proctoring pipeline (initialize camera and display)
        
        Returns:
            bool: True if started successfully
        """
        return self.initialize()
    
    def stop(self):
        """
        Stop the proctoring pipeline (cleanup resources)
        """
        self.cleanup()
    
    def capture_frame(self):
        """
        Capture a frame from the camera
        
        Returns:
            Frame or None if capture failed
        """
        if not self.camera:
            return None
        
        success, frame = self.camera.read_frame()
        if not success:
            return None
        
        return frame
    
    def display_frame(self, frame):
        """
        Display a frame to the window
        
        Args:
            frame: Frame to display
        """
        if not self.display:
            return
        
        # Add FPS if enabled
        if self.config.SHOW_FPS:
            # Calculate FPS (simple moving average)
            if not hasattr(self, '_fps_start_time'):
                self._fps_start_time = time.time()
                self._fps_frame_count = 0
            
            self._fps_frame_count += 1
            elapsed = time.time() - self._fps_start_time
            
            if elapsed > 1.0:
                fps = self._fps_frame_count / elapsed
                self.display.show_frame(frame, fps=fps)
                self._fps_frame_count = 0
                self._fps_start_time = time.time()
            else:
                self.display.show_frame(frame)
        else:
            self.display.show_frame(frame)
    
    def cleanup(self):
        """Cleanup resources (override from CameraPipeline)"""
        print("\n[DEBUG] === ENTERING ProctorPipeline.cleanup() ===")
        print("[DEBUG] Step 0: Starting cleanup")
        
        try:
            print("[DEBUG] Step 1: Generating final report")
            # Generate final report
            self.logger.info("Generating final proctoring report...")
            report = self.get_proctoring_report()
            
            print("[DEBUG] Step 2: Logging report stats")
            self.logger.info("=" * 60)
            self.logger.info("PROCTORING SESSION REPORT")
            self.logger.info("=" * 60)
            self.logger.info(f"Total Frames Captured: {report['session_stats']['total_frames_captured']}")
            self.logger.info(f"Total Frames Processed: {report['session_stats']['total_frames_processed']}")
            self.logger.info(f"Processing Ratio: {report['session_stats']['processing_ratio']:.2%}")
            self.logger.info(f"Total Alerts: {len(report['alerts'])}")
            
            if report['alert_summary']:
                self.logger.info("\nAlert Summary:")
                for alert_type, count in report['alert_summary'].items():
                    self.logger.info(f"  - {alert_type}: {count}")
            
            self.logger.info("=" * 60)
            print("[DEBUG] Step 3: Report generation complete")
        except Exception as e:
            print(f"[DEBUG] ERROR in report generation: {e}")
            self.logger.error(f"Error generating final report: {e}")
        
        # Close session logger and save
        try:
            print("[DEBUG] Step 4: Checking session logger")
            if hasattr(self, 'session_logger') and self.session_logger:
                print("[DEBUG] Step 5: Getting session summary")
                summary = self.session_logger.get_session_summary()
                self.logger.info(f"Session logs saved to: {summary['log_file']}")
                self.logger.info(f"Session alerts saved to: {summary['alerts_file']}")
                print("[DEBUG] Step 6: Closing session logger")
                self.session_logger.close()
                print("[DEBUG] Step 7: Session logger closed")
        except Exception as e:
            print(f"[DEBUG] ERROR closing session logger: {e}")
            self.logger.error(f"Error closing session logger: {e}")
        
        # Cleanup all registered detectors
        try:
            print("[DEBUG] Step 8: Checking detectors")
            if hasattr(self, 'detectors') and self.detectors:
                print(f"[DEBUG] Step 9: Found {len(self.detectors)} detectors to clean")
                self.logger.info("Cleaning up registered detectors...")
                # Create a list copy to avoid modifying dict during iteration
                detector_items = list(self.detectors.items())
                print(f"[DEBUG] Step 10: Created detector list copy with {len(detector_items)} items")
                
                for idx, (detector_name, detector) in enumerate(detector_items):
                    try:
                        print(f"[DEBUG] Step 11.{idx}: Cleaning detector '{detector_name}'")
                        if hasattr(detector, 'cleanup') and callable(detector.cleanup):
                            self.logger.info(f"Cleaning up {detector_name}...")
                            print(f"[DEBUG] Step 12.{idx}: Calling cleanup() on '{detector_name}'")
                            detector.cleanup()
                            print(f"[DEBUG] Step 13.{idx}: Cleanup completed for '{detector_name}'")
                        else:
                            print(f"[DEBUG] Step 12.{idx}: No cleanup method for '{detector_name}'")
                            self.logger.warning(f"{detector_name} has no cleanup method")
                    except Exception as e:
                        print(f"[DEBUG] ERROR cleaning up {detector_name}: {e}")
                        self.logger.error(f"Error cleaning up {detector_name}: {e}", exc_info=True)
                
                print("[DEBUG] Step 14: Clearing detectors dict")
                self.detectors.clear()
                print("[DEBUG] Step 15: Detectors cleared")
                self.logger.info("All detectors cleaned up")
        except Exception as e:
            print(f"[DEBUG] ERROR during detector cleanup: {e}")
            self.logger.error(f"Error during detector cleanup: {e}", exc_info=True)
        
        # Call parent cleanup (camera and display)
        try:
            print("[DEBUG] Step 16: Calling parent (CameraPipeline) cleanup")
            super().cleanup()
            print("[DEBUG] Step 17: Parent cleanup returned")
        except Exception as e:
            print(f"[DEBUG] ERROR in parent cleanup: {e}")
            self.logger.error(f"Error in parent cleanup: {e}", exc_info=True)
        
        print("[DEBUG] === EXITING ProctorPipeline.cleanup() ===")
