"""
Pipeline Module
Base camera pipeline and eye movement detection pipeline

Eye Movement Detection Pipeline
"""
import cv2
import logging
import time
from .camera_input import CameraCapture
from .display import DisplayWindow
from .config import Config
from .eye_detector import EyeMovementDetector


class CameraPipeline:
    """Main pipeline class that orchestrates camera capture and display"""
    
    def __init__(self, config=None):
        """
        Initialize the camera pipeline
        
        Args:
            config: Configuration object (uses default Config if None)
        """
        self.config = config or Config()
        self.camera = None
        self.display = None
        self.is_running = False
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging for the pipeline"""
        if self.config.ENABLE_LOGGING:
            logging.basicConfig(
                level=getattr(logging, self.config.LOG_LEVEL),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
    
    def initialize(self):
        """Initialize camera and display components"""
        logging.info("Initializing camera pipeline...")
        
        # Initialize camera
        self.camera = CameraCapture(
            camera_id=self.config.CAMERA_ID,
            width=self.config.CAMERA_WIDTH,
            height=self.config.CAMERA_HEIGHT,
            fps=self.config.CAMERA_FPS
        )
        
        if not self.camera.start():
            logging.error("Failed to start camera")
            return False
        
        # Initialize display
        self.display = DisplayWindow(
            window_name=self.config.WINDOW_NAME,
            fullscreen=self.config.FULLSCREEN
        )
        
        if not self.display.create_window():
            logging.error("Failed to create display window")
            self.camera.stop()
            return False
        
        logging.info("Pipeline initialized successfully")
        return True
    
    def process_frame(self, frame):
        """
        Process a single frame (override this method for custom processing)
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processed frame
        """
        # Default: no processing, just return the frame
        return frame
    
    def run(self):
        """Main pipeline loop"""
        if not self.initialize():
            logging.error("Pipeline initialization failed")
            return
        
        self.is_running = True
        logging.info("Starting pipeline loop...")
        
        # FPS tracking
        fps = 0
        frame_count = 0
        start_time = time.time()
        frame_time = 1.0 / self.config.MAX_FPS if self.config.MAX_FPS > 0 else 0
        
        try:
            while self.is_running:
                loop_start = time.time()
                
                # Read frame from camera
                success, frame = self.camera.read_frame()
                
                if not success:
                    logging.warning("Failed to read frame, continuing...")
                    continue
                
                # Process frame (can be overridden)
                processed_frame = self.process_frame(frame)
                
                # Display frame
                if self.config.SHOW_FPS:
                    self.display.show_frame(processed_frame, fps=fps)
                else:
                    self.display.show_frame(processed_frame)
                
                # Check for exit key
                if self.display.check_exit_key(1):
                    logging.info("Exit key pressed")
                    break
                
                # Calculate FPS
                frame_count += 1
                elapsed = time.time() - start_time
                if elapsed > 1.0:
                    fps = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
                
                # Frame rate limiting
                if frame_time > 0:
                    processing_time = time.time() - loop_start
                    sleep_time = frame_time - processing_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logging.info("Pipeline interrupted by user")
        
        except Exception as e:
            logging.error(f"Pipeline error: {e}", exc_info=True)
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logging.info("Cleaning up pipeline resources...")
        self.is_running = False
        
        if self.camera:
            self.camera.stop()
        
        if self.display:
            self.display.destroy_all()
        
        logging.info("Pipeline cleanup complete")


class EyeMovementPipeline(CameraPipeline):
    """Pipeline with integrated eye movement detection"""
    
    def __init__(self, config=None):
        """Initialize pipeline with eye movement detection"""
        super().__init__(config)
        self.eye_detector = None
        self.detection_count = 0
        self.movement_history = []
        self.max_history = 30  # Keep last 30 detections
        
    def initialize(self):
        """Initialize camera, display, and eye movement detector"""
        # Initialize base components
        if not super().initialize():
            return False
        
        # Initialize eye movement detector
        logging.info("Initializing eye movement detector...")
        
        self.eye_detector = EyeMovementDetector(
            model_path=self.config.EYE_MODEL_PATH,
            confidence_threshold=self.config.EYE_CONFIDENCE_THRESHOLD
        )
        
        if not self.eye_detector.load_models():
            logging.error("Failed to load eye movement detection models")
            return False
        
        logging.info("Eye movement detector initialized successfully")
        return True
    
    def process_frame(self, frame):
        """
        Process frame with eye movement detection
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processed frame with eye movement annotations
        """
        if self.eye_detector is None:
            return frame
        
        # Detect eye movements and draw results
        processed_frame, detections = self.eye_detector.process_frame(
            frame,
            draw=True,
            color=self.config.EYE_BOX_COLOR,
            thickness=self.config.EYE_BOX_THICKNESS
        )
        
        # Update detection count
        self.detection_count = len(detections)
        
        # Store detection history
        if detections:
            for i, det in enumerate(detections):
                self.movement_history.append({
                    'timestamp': time.time(),
                    'eye': f'eye_{i+1}',
                    'risk_status': det.get('risk_status', 'Unknown'),
                    'risk_score': det.get('risk_score', 0.0)
                })
            
            # Keep only recent history
            if len(self.movement_history) > self.max_history:
                self.movement_history = self.movement_history[-self.max_history:]
        
        # Add detection count to display
        cv2.putText(
            processed_frame,
            f"Eyes Detected: {self.detection_count}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )
        
        # Display risk scores for each detection (Developer Info)
        if detections:
            risk_scores_text = "Risk Scores: "
            for i, det in enumerate(detections):
                score = det.get('risk_score', 0.0)
                risk_scores_text += f"Eye{i+1}={score:.2f} "
            
            cv2.putText(
                processed_frame,
                risk_scores_text,
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 100, 255),  # Pink color for developer info
                2
            )
            y_offset = 150  # Start eye status below risk scores
        else:
            y_offset = 110
        
        # Display current eye risk status (summary on left side)
        for i, det in enumerate(detections):
            risk_status = det.get('risk_status', 'Unknown')
            risk_score = det.get('risk_score', 0.0)
            
            # Color based on risk
            if 'RISK' in risk_status:
                text_color = (0, 0, 255)  # Red
            elif 'THINKING' in risk_status:
                text_color = (0, 165, 255)  # Orange
            elif 'SAFE' in risk_status:
                text_color = (0, 255, 0)  # Green
            else:
                text_color = (255, 255, 0)  # Yellow
            
            text = f"Eye {i+1}: {risk_status}"
            cv2.putText(
                processed_frame,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                text_color,
                2
            )
            y_offset += 30
        
        # Show keypoint legend
        if detections and self.config.EYE_SHOW_KEYPOINTS:
            legend_y = processed_frame.shape[0] - 100
            cv2.putText(processed_frame, "Keypoints:", (10, legend_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(processed_frame, "I=Inner (Caruncle)", (10, legend_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.putText(processed_frame, "O=Outer (Margin)", (10, legend_y + 45),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
            cv2.putText(processed_frame, "P=Pupil (Center)", (10, legend_y + 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        return processed_frame
    
    def get_movement_statistics(self):
        """Get statistics about eye movements and risk status"""
        if not self.movement_history:
            return {}
        
        # Count risk status types
        status_counts = {}
        for entry in self.movement_history:
            status = entry['risk_status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate average FPS
        total_time = 0
        if len(self.movement_history) > 1:
            total_time = self.movement_history[-1]['timestamp'] - self.movement_history[0]['timestamp']
        avg_fps = len(self.movement_history) / total_time if total_time > 0 else 0
        
        return {
            'total_detections': len(self.movement_history),
            'movement_counts': status_counts,
            'recent_movements': self.movement_history[-5:],  # Last 5 movements
            'avg_fps': avg_fps
        }
