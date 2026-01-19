"""
Pipeline Module
Base camera pipeline class

YOLOv8 Face Detection Pipeline

"""
import cv2
import logging
import time
from .camera_input import CameraCapture
from .display import DisplayWindow
from .config import Config
from .face_detector import YOLOv8Detector

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


class FaceDetectionPipeline(CameraPipeline):
    """Pipeline with integrated YOLOv8 face detection"""
    
    def __init__(self, config=None):
        """Initialize pipeline with face detection"""
        super().__init__(config)
        self.face_detector = None
        self.face_count = 0
        
    def initialize(self):
        """Initialize camera, display, and face detector"""
        # Initialize base components
        if not super().initialize():
            return False
        
        # Initialize face detector
        logging.info("Initializing face detector...")
        
        if self.config.FACE_MODEL_TYPE == "yolov8":
            self.face_detector = YOLOv8Detector(
                model_name=self.config.FACE_MODEL_NAME,
                confidence_threshold=self.config.FACE_CONFIDENCE_THRESHOLD
            )
        else:
            from modules import HaarCascadeFaceDetector
            self.face_detector = HaarCascadeFaceDetector()
        
        if not self.face_detector.load_model():
            logging.error("Failed to load face detection model")
            return False
        
        logging.info("Face detector initialized successfully")
        return True
    
    def process_frame(self, frame):
        """
        Process frame with face detection
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Processed frame with face bounding boxes
        """
        if self.face_detector is None:
            return frame
        
        # Detect faces and draw bounding boxes
        processed_frame, faces = self.face_detector.process_frame(
            frame,
            draw=True,
            color=self.config.FACE_BOX_COLOR,
            thickness=self.config.FACE_BOX_THICKNESS
        )
        
        # Update face count
        self.face_count = len(faces)
        
        # Add face count to display
        cv2.putText(
            processed_frame,
            f"Faces: {self.face_count}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            2
        )
        
        return processed_frame

