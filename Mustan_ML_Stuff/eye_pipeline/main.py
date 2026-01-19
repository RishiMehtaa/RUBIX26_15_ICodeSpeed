"""
Main Application - 
Real-time eye movement detection using camera feed
"""

from modules import EyeMovementPipeline, Config


def main():
    """Main entry point"""
    # Configure pipeline
    Config.WINDOW_NAME = "Eye Gaze Risk Analysis - best.pt"
    Config.EYE_DETECTION_ENABLED = True
    Config.EYE_MODEL_PATH = "best.pt"  # YOLOv8 pose model with keypoints (in same directory)
    Config.EYE_CONFIDENCE_THRESHOLD = 0.25  # Lowered for better detection
    Config.EYE_BOX_COLOR = (255, 0, 0)  # Blue (will change based on risk)
    Config.EYE_BOX_THICKNESS = 2
    Config.EYE_SHOW_CONFIDENCE = True
    Config.EYE_SHOW_LABEL = True
    Config.EYE_SHOW_KEYPOINTS = True
    
    Config.FACE_DETECTION_ENABLED = False  # Not needed with best.pt
    Config.FACE_MODEL_NAME = "yolov8n.pt"
    Config.FACE_CONFIDENCE_THRESHOLD = 0.5
    
    # Create and run pipeline
    pipeline = EyeMovementPipeline()
    
    print("\n" + "="*70)
    print("Eye Gaze Detection & Risk Analysis - Using YOLOv8-Pose")
    print("="*70)
    print("Starting eye detection with gaze-based risk assessment...")
    print("\nModel: best.pt (YOLOv8n-pose)")
    print("  - Detects eyes with 3 keypoints:")
    print("    • Inner Corner (I) - Caruncle")
    print("    • Outer Corner (O) - Interior margin")
    print("    • Pupil Center (P) - Iris center")
    print("\nRisk Status Categories:")
    print("  🟢 CENTER (SAFE)         - Focused on screen")
    print("  🔴 LOOKING DOWN (RISK)   - Potential phone/notes usage")
    print("  🟠 LOOKING UP (THINKING) - Acceptable behavior")
    print("  🔴 LOOKING SIDE (RISK)   - Significant distraction")
    print("\nRisk Calculation:")
    print("  - Based on geometric analysis of pupil position")
    print("  - Vertical ratio > 0.15: Looking down (risk)")
    print("  - Horizontal ratio < 0.3 or > 0.7: Looking side (risk)")
    print("\nControls:")
    print("  - Press 'q' or ESC to quit")
    print("\nNote: Ensure best.pt is in eye_pipeline directory")
    print("="*70 + "\n")
    
    try:
        pipeline.run()
        
        # Print statistics after exit
        print("\n" + "="*70)
        print("Session Statistics")
        print("="*70)
        stats = pipeline.get_movement_statistics()
        
        if stats:
            print(f"Total Eye Detections: {stats.get('total_detections', 0)}")
            print(f"Average FPS: {stats.get('avg_fps', 0):.1f}")
            print("\nRisk Status Distribution:")
            for status, count in stats.get('movement_counts', {}).items():
                print(f"  {status}: {count}")
        else:
            print("No detections recorded")
        
        print("="*70 + "\n")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
