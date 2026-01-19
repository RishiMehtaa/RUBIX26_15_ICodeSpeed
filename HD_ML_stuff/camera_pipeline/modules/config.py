"""
Configuration Module
Central configuration for camera pipeline
"""


class Config:
    """Pipeline configuration settings"""
    
    # Camera Settings
    CAMERA_ID = 0
    CAMERA_WIDTH = 1080
    CAMERA_HEIGHT = 720
    CAMERA_FPS = 30
    
    # Display Settings
    WINDOW_NAME = "Camera Pipeline"
    FULLSCREEN = False
    SHOW_FPS = True
    
    # Pipeline Settings
    ENABLE_LOGGING = True
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    
    # Performance Settings
    MAX_FPS = 60  # Maximum FPS to process
    FRAME_SKIP = 0  # Number of frames to skip (0 = no skip)
    
    # Face Detection Settings
    FACE_DETECTION_ENABLED = True
    FACE_MODEL_TYPE = "yolov8"  # "yolov8" or "haar"
    FACE_MODEL_NAME = "yolov8s.pt"  # Standard YOLOv8 model
    FACE_CONFIDENCE_THRESHOLD = 0.5
    FACE_TARGET_CLASSES = [0]  # Class ID for 'person' in COCO
    FACE_BOX_COLOR = (0, 255, 0)  # Green (B, G, R)
    FACE_BOX_THICKNESS = 2
    FACE_SHOW_CONFIDENCE = True
    
    @classmethod
    def from_dict(cls, config_dict):
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)
    
    @classmethod
    def to_dict(cls):
        """Convert configuration to dictionary"""
        return {
            key: value
            for key, value in cls.__dict__.items()
            if not key.startswith('_') and key.isupper()
        }
