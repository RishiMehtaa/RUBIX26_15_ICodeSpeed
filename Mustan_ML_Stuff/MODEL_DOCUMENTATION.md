# Best.pt Model Documentation

Complete technical documentation for the custom-trained YOLOv8 pose estimation model used for eye gaze detection and risk analysis.

## Model Overview

- **Model Name**: `best.pt`
- **Base Architecture**: YOLOv8n-pose (Pose Estimation)
- **Framework**: Ultralytics YOLOv8
- **Training Notebook**: `eye-detection-using-yolov8-mustansirhy.ipynb`
- **Purpose**: Real-time eye detection with keypoint tracking for gaze-based risk assessment

## Model Specifications

### Input Format
- **Image Size**: 640x640 pixels
- **Color Space**: RGB/BGR
- **Preprocessing**: Automatic (handled by YOLO)
- **Batch Size**: Variable (1 for real-time inference)

### Output Format

#### Detection Output
Each detection contains:
- **Bounding Box**: (x1, y1, x2, y2) - Eye region coordinates
- **Confidence**: Float (0.0 - 1.0)
- **Class**: Single class "eye" (class_id: 0)
- **Keypoints**: 3 keypoints per eye

#### Keypoint Structure
Shape: `(N, 3, 2)` where N = number of detected eyes

Each keypoint has:
- **X coordinate**: Pixel position (0 to image_width)
- **Y coordinate**: Pixel position (0 to image_height)
- **Visibility**: Confidence score (0.0 - 1.0)

**Keypoint Order** (Critical for correct interpretation):
1. **Keypoint 0**: Inner corner (caruncle)
2. **Keypoint 1**: Outer corner (interior margin point 8)
3. **Keypoint 2**: Pupil center (average of all iris points)

### Model Configuration (YAML)

```yaml
path: /kaggle/working/eye_dataset_full
train: images
val: images
kpt_shape: [3, 3]  # 3 keypoints × 3 values (x, y, visibility)
flip_idx: [1, 0, 2]  # Swap inner/outer when horizontally flipped
names:
  0: eye
```

## Training Data Format

### JSON Structure

The training data consists of JSON files with detailed eye landmark annotations:

```json
{
  "interior_margin_2d": [
    "(251.5525, 233.6851, 9.6326)",  // Point 0
    "(249.3537, 239.9289, 9.7528)",  // Point 1
    // ... 14 more points
    "(375.3914, 234.2160, 9.2345)"   // Point 8 (used as outer corner)
  ],
  "caruncle_2d": [
    "(236.7794, 224.1939, 9.7077)",  // Point 0 (used as inner corner)
    // ... 6 more points
  ],
  "iris_2d": [
    "(288.0029, 265.9630, 9.0166)",
    "(288.6189, 271.6601, 9.0583)",
    // ... 30 more points (all averaged for pupil center)
  ],
  "eye_details": {
    "look_vec": "(-0.0015, 0.4025, -0.9154, 0.0000)",
    "pupil_size": "0.0123414",
    "iris_size": "0.9058223"
  }
}
```

### Keypoint Extraction Logic

From the training notebook (`create_label` function):

```python
def create_label(json_path, image_width, image_height):
    # 1. Extract inner corner
    inner = parse_coord(data['caruncle_2d'][0])
    
    # 2. Extract outer corner
    outer = parse_coord(data['interior_margin_2d'][8])
    
    # 3. Calculate pupil center (average of all iris points)
    iris_points = [parse_coord(p) for p in data['iris_2d']]
    pupil_x = sum(p[0] for p in iris_points) / len(iris_points)
    pupil_y = sum(p[1] for p in iris_points) / len(iris_points)
    
    # 4. Normalize to image dimensions
    points = [inner, outer, (pupil_x, pupil_y)]
    norm_points = [(p[0]/image_width, p[1]/image_height) for p in points]
    
    # 5. Calculate bounding box (1.5x expansion)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    w = (max(xs) - min(xs)) * 1.5
    h = (max(ys) - min(ys)) * 1.5
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    
    # 6. Write in YOLO format (14 columns)
    # Format: class cx cy w h kpt1_x kpt1_y kpt1_v kpt2_x kpt2_y kpt2_v kpt3_x kpt3_y kpt3_v
    kpt_str = " ".join([f"{p[0]} {p[1]} 1" for p in norm_points])
    return f"0 {cx/image_width} {cy/image_height} {w/image_width} {h/image_height} {kpt_str}"
```

## Training Configuration

### Training Parameters

```python
model.train(
    data='eye_pose_full.yaml', 
    epochs=50, 
    imgsz=640,
    batch=16,
    project='/kaggle/working/runs_full',
    
    # Data Augmentation (for webcam robustness)
    hsv_h=0.015,    # Color variation (different skin tones)
    hsv_s=0.7,      # Saturation (bad webcams)
    hsv_v=0.4,      # Brightness (dark rooms)
    degrees=10,     # Rotation (head tilt)
    scale=0.5,      # Zoom (camera distance)
    mosaic=1.0,     # Multi-image mixing
    blur=2.0,       # Blur (out-of-focus camera)
    noise=0.1       # Noise (low-light sensor)
)
```

### Dataset Statistics
- **Total Samples**: 5,000 images
- **Sources**: TestSet + ImprovementSet
- **Training Split**: images/ (used for both train and val)
- **File Format**: Symlinks to original images + generated .txt labels

## Risk Analysis Algorithm

### Geometric Calculation

The model outputs keypoints, and risk is calculated post-detection using geometry:

```python
def calculate_risk(keypoints):
    """
    Expects keypoints: (3, 2) -> [(inner_x, inner_y), (outer_x, outer_y), (pupil_x, pupil_y)]
    """
    inner, outer, pupil = keypoints[0], keypoints[1], keypoints[2]
    
    # 1. Calculate eye width
    eye_width = abs(outer[0] - inner[0]) + 1e-6
    
    # 2. Vertical ratio (pupil Y vs eye center Y)
    eye_center_y = (inner[1] + outer[1]) / 2
    vertical_ratio = (pupil[1] - eye_center_y) / eye_width
    
    # 3. Horizontal ratio (pupil position)
    horizontal_ratio = (pupil[0] - inner[0]) / eye_width
    
    # 4. Classify
    if vertical_ratio > 0.15:
        return "LOOKING DOWN (RISK)"  # Phone/notes
    elif vertical_ratio < -0.15:
        return "LOOKING UP (THINKING)"  # Acceptable
    elif horizontal_ratio < 0.3 or horizontal_ratio > 0.7:
        return "LOOKING SIDE (RISK)"  # Distracted
    else:
        return "CENTER (SAFE)"  # Focused
```

### Threshold Values

| Metric | Threshold | Meaning |
|--------|-----------|---------|
| `vertical_ratio > 0.15` | Looking down significantly | High risk (phone/notes) |
| `vertical_ratio < -0.15` | Looking up significantly | Safe (thinking) |
| `horizontal_ratio < 0.3` | Pupil too far left | Medium risk (side glance) |
| `horizontal_ratio > 0.7` | Pupil too far right | Medium risk (side glance) |
| Otherwise | Center position | Safe (focused) |

## Using the Model

### Loading the Model

```python
from ultralytics import YOLO

# Load model
model = YOLO('best.pt')

# Run inference
results = model.predict(source=frame, imgsz=640, verbose=False, conf=0.5)
```

### Extracting Keypoints

```python
for result in results:
    # Check if keypoints exist
    if result.keypoints is not None and len(result.keypoints.xy) > 0:
        # Get keypoints for first detected eye
        keypoints = result.keypoints.xy[0].cpu().numpy()  # Shape: (3, 2)
        
        # Extract individual keypoints
        inner_corner = keypoints[0]  # (x, y)
        outer_corner = keypoints[1]  # (x, y)
        pupil_center = keypoints[2]  # (x, y)
        
        # Get visibility scores (if available)
        if hasattr(result.keypoints, 'conf'):
            visibility = result.keypoints.conf[0].cpu().numpy()  # Shape: (3,)
```

### Complete Pipeline Example

```python
import cv2
from ultralytics import YOLO

# Initialize
model = YOLO('best.pt')
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run detection
    results = model.predict(frame, verbose=False, conf=0.5)
    
    for result in results:
        # Get keypoints
        if result.keypoints is not None and len(result.keypoints.xy) > 0:
            kpts = result.keypoints.xy[0].cpu().numpy()
            
            # Calculate risk
            status, score = calculate_risk(kpts)
            
            # Visualize
            annotated = result.plot()  # Draws boxes and keypoints
            cv2.imshow('Eye Detection', annotated)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

## Performance Metrics

From training logs:
- **Mean Average Precision (Pose)**: Logged in validation
- **Box Loss**: Bounding box accuracy
- **Pose Loss**: Keypoint localization accuracy

To view metrics:
```python
metrics = model.val(split='val')
print(f"mAP50: {metrics.box.map50:.4f}")
```

## Important Notes

### ⚠️ Critical Implementation Details

1. **Keypoint Order is Fixed**: Always [inner, outer, pupil]
   - Do NOT assume other orderings
   - Swapping breaks risk calculation

2. **Coordinate System**: 
   - Origin (0,0) is top-left
   - Y increases downward (positive = down)
   - This affects vertical ratio interpretation

3. **Visibility Threshold**: 
   - Keypoints with visibility < 0.3 are considered occluded
   - Handle low-visibility keypoints gracefully

4. **Model Path**: 
   - In pipeline: Use `../best.pt` (relative to eye_pipeline/)
   - In root: Use `best.pt`

5. **No Classification Head**: 
   - Model does NOT classify gaze direction
   - Classification happens post-detection via geometry
   - Do not look for movement classes in model output

### 🎯 Best Practices

- Use `conf=0.5` for balanced detection
- Process frames at 640x640 for optimal performance
- Check keypoint visibility before calculation
- Handle cases where no eyes are detected
- Color-code risk levels for user feedback

## References

- **Training Notebook**: `eye-detection-using-yolov8-mustansirhy.ipynb`
- **Model File**: `best.pt`
- **Configuration**: `eye_pose_full.yaml`
- **Ultralytics Docs**: https://docs.ultralytics.com/models/yolov8/
