# Eye Gaze Detection & Risk Analysis Pipeline

A modular real-time pipeline for eye detection and gaze-based risk assessment using YOLOv8 pose estimation with keypoint tracking.

## Features

- **Keypoint-Based Eye Detection**: Detects eyes with 3 keypoints per eye:
  - Inner corner (caruncle)
  - Outer corner (interior margin)
  - Pupil center (iris center)

- **Geometric Risk Analysis**: Analyzes gaze direction using pupil position geometry:
  - `CENTER (SAFE)` - User focused on screen
  - `LOOKING DOWN (RISK)` - Potential phone/notes usage
  - `LOOKING UP (THINKING)` - Acceptable behavior
  - `LOOKING SIDE (RISK)` - Significant distraction

- **Real-time Processing**: Optimized for live webcam feed
- **Modular Architecture**: Separate modules for camera, display, detection, and configuration
- **FPS Display**: Real-time performance monitoring
- **Context Manager Support**: Automatic resource cleanup
- **Color-Coded Alerts**: Visual risk indicators (Green=Safe, Red=Risk, Orange=Thinking)

## Project Structure

```
eye_pipeline/
├── main.py                      # Main application entry point
├── modules/
│   ├── __init__.py             # Module exports
│   ├── pipeline.py             # Base CameraPipeline & EyeMovementPipeline
│   ├── camera_input.py         # Camera capture module
│   ├── display.py              # Display window module
│   ├── eye_detector.py         # Eye detection & risk analysis module
│   └── config.py               # Configuration settings
└── README.md                    # This file
```

## How It Works

### Model Architecture

**YOLOv8n-pose** trained on eye gaze detection dataset:
- **Input**: 640x640 RGB images
- **Output**: Bounding boxes + 3 keypoints per eye
- **Training**: Based on `eye-detection-using-yolov8-mustansirhy.ipynb`

### Risk Calculation Algorithm

From the training notebook, risk is calculated using geometric analysis:

```python
# 1. Calculate eye width (distance between corners)
eye_width = abs(outer_x - inner_x)

# 2. Vertical ratio (pupil vs eye center)
eye_center_y = (inner_y + outer_y) / 2
vertical_ratio = (pupil_y - eye_center_y) / eye_width

# 3. Horizontal ratio (pupil position)
horizontal_ratio = (pupil_x - inner_x) / eye_width

# 4. Classify based on thresholds:
# - vertical_ratio > 0.15: LOOKING DOWN (RISK)
# - vertical_ratio < -0.15: LOOKING UP (THINKING)
# - horizontal_ratio < 0.3 or > 0.7: LOOKING SIDE (RISK)
# - else: CENTER (SAFE)
```

### Architecture Overview

1. **Camera Input Module** (`camera_input.py`)
   - Captures frames from webcam
   - Manages camera lifecycle
   - Configurable resolution and FPS

2. **Eye Detector Module** (`eye_detector.py`)
   - Loads best.pt YOLOv8-pose model
   - Detects eyes with keypoints
   - Calculates risk status using geometry
   - Annotates frames with color-coded results

3. **Display Module** (`display.py`)
   - Creates and manages display window
   - Renders processed frames with annotations
   - Handles user input (ESC/Q to quit)

4. **Pipeline Module** (`pipeline.py`)
   - Orchestrates the entire processing flow
   - Manages frame loop and FPS calculation
   - Coordinates camera → detection → display

5. **Main Application** (`main.py`)
   - Initializes and configures the pipeline
   - Runs detection loop
   - Provides session statistics

### Detection Flow

```
Webcam → Capture Frame → YOLO Detection → Extract Keypoints →
Calculate Risk (Geometry) → Color-Code Result → Annotate → Display
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- Webcam or camera device
- Virtual environment (recommended)

### Step 1: Install Dependencies

```bash
# Navigate to Mustan_ML_Stuff directory
cd Mustan_ML_Stuff

# Install requirements
pip install -r requirements_yolo.txt
```

### Step 2: Run the Pipeline

```bash
# Navigate to eye_pipeline directory
cd eye_pipeline

# Run the application
python main.py
```

## Usage

### Basic Usage

```python
from modules import EyeMovementPipeline, Config

# Configure pipeline
Config.EYE_MODEL_PATH = None  # or path to your trained model
Config.EYE_CONFIDENCE_THRESHOLD = 0.4
Config.FACE_MODEL_NAME = "yolov8n.pt"

# Create and run pipeline
pipeline = EyeMovementPipeline()
pipeline.run()

# Get statistics after exit
stats = pipeline.get_movement_statistics()
print(stats)
```

### Custom Configuration

```python
from modules import Config

# Camera settings
Config.CAMERA_ID = 0
Config.CAMERA_WIDTH = 1280
Config.CAMERA_HEIGHT = 720

# Detection settings
Config.EYE_CONFIDENCE_THRESHOLD = 0.6
Config.EYE_BOX_COLOR = (255, 0, 0)  # Blue

# Face detection
Config.FACE_MODEL_NAME = "yolov8n-face.pt"  # Better face detection
```

## Classification Methods

### 1. ML-Based Classification (Recommended)

If you have a trained PyTorch model:

```python
Config.EYE_MODEL_PATH = "path/to/your/eye_movement_model.pth"
```

The model should:
- Accept 224×224 RGB images
- Output 10 classes
- Be normalized with ImageNet mean/std

### 2. Heuristic-Based Classification (Default)

Uses computer vision techniques:
- Converts eye region to grayscale
- Detects iris/pupil using thresholding
- Calculates iris position
- Classifies based on position thresholds

Works without any training data but less accurate than ML models.

## Training Your Own Model

To train a custom eye movement classification model:

1. **Collect Dataset**
   - Capture images of eyes in each of the 10 positions
   - Aim for 500+ images per class
   - Ensure diverse lighting and subjects

2. **Label Dataset**
   - Organize images into class folders
   - Use standard image classification format

3. **Train Model**
   ```python
   # Use PyTorch to train a classifier
   # See model_inspector.py for model loading examples
   ```

4. **Export Model**
   ```python
   torch.save(model, 'eye_movement_model.pth')
   ```

5. **Use in Pipeline**
   ```python
   Config.EYE_MODEL_PATH = "eye_movement_model.pth"
   ```

## Performance Optimization

### Speed Optimization

```python
# Use smaller face detection model
Config.FACE_MODEL_NAME = "yolov8n.pt"  # Fastest

# Increase confidence threshold
Config.EYE_CONFIDENCE_THRESHOLD = 0.6

# Limit FPS
Config.MAX_FPS = 30
```

### Accuracy Optimization

```python
# Use better face detection model
Config.FACE_MODEL_NAME = "yolov8n-face.pt"

# Lower confidence threshold
Config.EYE_CONFIDENCE_THRESHOLD = 0.4

# Train custom classification model
Config.EYE_MODEL_PATH = "your_trained_model.pth"
```

## Features & Capabilities

### Real-time Detection
- Detects multiple faces simultaneously
- Processes both left and right eyes
- Displays current eye movement state

### Movement Tracking
- Maintains history of last 30 detections
- Provides movement statistics
- Tracks confidence scores

### Visual Feedback
- Face bounding boxes (green)
- Eye region boxes (blue)
- Movement labels with confidence
- FPS counter
- Detection count

## Troubleshooting

### Issue: No faces detected
- **Solution**: Ensure good lighting and face is visible
- Try lowering `FACE_CONFIDENCE_THRESHOLD`
- Check camera is working

### Issue: Inaccurate eye movement classification
- **Solution**: Train a custom ML model
- Adjust heuristic thresholds in `_heuristic_classification()`
- Ensure eyes are clearly visible

### Issue: Low FPS
- **Solution**: Use smaller YOLOv8 model (yolov8n)
- Reduce camera resolution
- Increase `MAX_FPS` limit

### Issue: Model file not found
- **Solution**: Set `EYE_MODEL_PATH = None` to use heuristics
- Or provide correct path to your trained model

## Applications

1. **Gaze Tracking**: Monitor where users are looking
2. **Attention Monitoring**: Detect if person is focused
3. **Drowsiness Detection**: Alert when eyes are closed
4. **Accessibility**: Control interfaces with eye movements
5. **Research**: Study eye movement patterns
6. **Gaming**: Eye-controlled gameplay
7. **Medical**: Diagnose eye movement disorders

## Comparison with Face Detection Pipeline

| Feature | Face Pipeline (HD_ML_stuff) | Eye Pipeline (Mustan_ML_Stuff) |
|---------|---------------------------|-------------------------------|
| Primary Task | Face Detection | Eye Movement Classification |
| Classes | 1 (Face/Person) | 10 (Eye Positions) |
| Model | YOLOv8 | YOLOv8 + Custom Classifier |
| Output | Face bounding boxes | Eye positions + movements |
| Use Case | Identify faces | Analyze eye movements |

## Next Steps

1. **Collect Training Data**: Build dataset for your use case
2. **Train Custom Model**: Improve classification accuracy
3. **Add Features**: Implement gaze tracking, blink detection
4. **Optimize Performance**: Profile and optimize bottlenecks
5. **Deploy**: Package for production use

## Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [OpenCV Documentation](https://docs.opencv.org/)
- Eye Movement Datasets: Search for "eye gaze datasets" or "eye movement datasets"

## License

This project is part of the RUBIX26_15_ICodeSpeed repository.
