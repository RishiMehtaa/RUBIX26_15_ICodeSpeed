# Mustan ML Stuff

Eye gaze detection and risk analysis using YOLOv8 pose estimation.

## Overview

This project implements real-time eye gaze tracking and risk assessment using a custom-trained YOLOv8-pose model. The model detects eyes and tracks 3 keypoints per eye to analyze gaze direction and identify potentially risky behavior (looking away from screen).

### Model Architecture

- **Model Type**: YOLOv8n-pose (Pose Estimation)
- **Input**: 640x640 RGB images
- **Output**: Eye detection with 3 keypoints per eye
  1. **Inner corner** (caruncle)
  2. **Outer corner** (interior margin)
  3. **Pupil center** (iris center)

### Training Data

The model was trained on eye gaze detection dataset with:
- **Data Format**: JSON files containing eye landmark coordinates
- **Keypoint Extraction**:
  - Inner corner: `caruncle_2d[0]`
  - Outer corner: `interior_margin_2d[8]`
  - Pupil: Average of all `iris_2d` points
- **Training Config**: `kpt_shape: [3, 3]` (3 keypoints × 3 values each)

## Projects

### 1. Eye Movement Detection Pipeline (Primary)
Real-time eye detection with gaze-based risk analysis using geometric calculations.
- 📁 Location: `eye_pipeline/`
- 📖 [View Documentation](eye_pipeline/README.md)
- ⚙️ Uses: `best.pt` model with keypoint detection

**Risk Analysis Categories**:
- `CENTER (SAFE)` - User focused on screen
- `LOOKING DOWN (RISK)` - Looking at phone/notes
- `LOOKING UP (THINKING)` - Looking up (acceptable)
- `LOOKING SIDE (RISK)` - Looking left/right significantly

### 2. Standalone Risk Analysis Script
Simple webcam script for testing the risk calculation logic.
- 📁 Location: `script.py`
- 📖 Based on: Training notebook logic

## Quick Start

```bash
# Install dependencies
pip install -r requirements_yolo.txt

# Run eye movement detection
cd eye_pipeline
python main.py

# Inspect a model
python test_pretrained_model.py

# Run eye tracking
python eye_detection_tracking.py
```

## Sharing Models with Collaborators

Models are ignored by default in `.gitignore` to prevent large files in git. Here are three ways to share models:

### Option 1: Whitelist Specific Models (Small Models < 100MB)

Edit `.gitignore` and uncomment specific models:
```gitignore
# Whitelist your model
!pretrainedModel.pth
!eye_movement_model.pth
!models/baseline_model.pth
```

Then commit normally:
```bash
git add pretrainedModel.pth
git commit -m "Add pretrained model"
git push
```

### Option 2: Git LFS (Recommended for Large Models)

Git Large File Storage handles large files efficiently:

```bash
# One-time setup
git lfs install

# Track model files
git lfs track "*.pth"
git lfs track "*.pt"

# Commit the tracking file
git add .gitattributes
git commit -m "Configure Git LFS"

# Add and commit models
git add models/
git commit -m "Add models via Git LFS"
git push
```

**Collaborators clone with:**
```bash
git lfs install
git clone <repository-url>
```

### Option 3: External Storage (Best for Very Large Models > 1GB)

Host models externally and provide download links:

**Popular Options:**
- 🔗 **Google Drive**: Public sharing link
- ☁️ **AWS S3**: Cloud storage with wget/curl
- 🤗 **HuggingFace Hub**: ML model hosting
- 📦 **GitHub Releases**: Attach to releases
- 🗄️ **Dropbox/OneDrive**: Shared folders

**Example: Create a download script**

Create `download_models.sh`:
```bash
#!/bin/bash
# Download pretrained model
wget -O pretrainedModel.pth "https://drive.google.com/uc?export=download&id=YOUR_FILE_ID"
echo "Model downloaded successfully!"
```

Or Python script `download_models.py`:
```python
import requests
import os

def download_model(url, filename):
    """Download model from URL"""
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"✓ {filename} downloaded!")

if __name__ == "__main__":
    # Add your model URLs
    models = {
        "pretrainedModel.pth": "YOUR_DOWNLOAD_URL",
        "eye_movement_model.pth": "YOUR_DOWNLOAD_URL"
    }
    
    for filename, url in models.items():
        if not os.path.exists(filename):
            download_model(url, filename)
        else:
            print(f"✓ {filename} already exists")
```

Then in your README, tell collaborators:
```bash
# Download models before running
python download_models.py
```

## Recommended Approach

| Model Size | Recommended Method | Why |
|-----------|-------------------|-----|
| < 10MB | Whitelist in git | Simple, no extra setup |
| 10MB - 100MB | Git LFS | Good balance, version controlled |
| > 100MB | External Storage | Faster clones, no size limits |

## Project Structure

```
Mustan_ML_Stuff/
├── README.md                        # This file
├── requirements_yolo.txt            # Dependencies
├── .gitignore                       # Git ignore rules
│
├── eye_pipeline/                    # Eye movement detection
│   ├── main.py
│   ├── README.md
│   └── modules/
│
├── eye_detection_tracking.py        # YOLOv8 eye tracking
├── eye_dataset_guide.md
│
├── model_inspector.py               # Model analysis tool
├── test_pretrained_model.py
├── README_model_inspector.md
│
├── example.py                       # Example scripts
└── fastapi.py
```

## Dependencies

All projects use the same dependencies:

```bash
pip install -r requirements_yolo.txt
```

Key packages:
- `ultralytics` - YOLOv8
- `torch` - PyTorch
- `opencv-python` - Computer vision
- `numpy` - Numerical computing
- `pillow` - Image processing

## Contributing

When contributing models or datasets:

1. **Small files (< 10MB)**: Commit directly
2. **Large files (> 10MB)**: Use Git LFS or external storage
3. **Datasets**: Always use external storage or DVC
4. **Update documentation**: Keep READMEs current

## License

Part of the RUBIX26_15_ICodeSpeed repository.
