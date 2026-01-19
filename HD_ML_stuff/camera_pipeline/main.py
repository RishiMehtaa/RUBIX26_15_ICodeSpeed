"""
Main Application - 
Real-time face detection using camera feed
"""

from modules import FaceDetectionPipeline, Config


def main():
    """Main entry point"""
    # Configure pipeline
    Config.WINDOW_NAME = "YOLOv8 Face Detection Pipeline"
    Config.FACE_DETECTION_ENABLED = True
    Config.FACE_MODEL_TYPE = "yolov8"
    Config.FACE_MODEL_NAME = "yolov8s"
    Config.FACE_CONFIDENCE_THRESHOLD = 0.5
    Config.FACE_BOX_COLOR = (0, 255, 0)  # Green
    Config.FACE_BOX_THICKNESS = 2
    Config.FACE_SHOW_CONFIDENCE = True
    
    # Create and run pipeline
    pipeline = FaceDetectionPipeline()
    
    print("\n" + "="*60)
    print("YOLOv8 Face Detection Pipeline")
    print("="*60)
    print("Starting face detection with YOLOv8...")
    print("\nControls:")
    print("  - Press 'q' or ESC to quit")
    print("\nNote: First run will download YOLOv8 face model (~6MB)")
    print("="*60 + "\n")
    
    pipeline.run()


if __name__ == "__main__":
    main()
