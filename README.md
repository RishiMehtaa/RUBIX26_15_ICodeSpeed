# AI Proctoring System - ICodeSpeed

## Overview

ICodeSpeed is an intelligent AI-powered proctoring system designed to ensure academic integrity during online examinations. The system combines a comprehensive web application with advanced machine learning models to monitor and detect suspicious behavior in real-time, providing administrators with detailed risk assessments of each test session.

## System Architecture

### Frontend Application (React + Electron)

The application is built using React and packaged as an Electron desktop application, providing a secure and controlled testing environment. The system supports two distinct user roles with specialized interfaces:

#### **Admin Interface**
- **Test Management**: Create, configure, and publish assessments
- **Results Dashboard**: View comprehensive student performance analytics
- **Proctoring Reports**: Access detailed risk scores and violation logs for each test session
- **User Management**: Monitor student accounts and test participation

#### **Student Interface**
- **Test Taking**: Access and complete published assessments
- **Performance Review**: View personal test scores and feedback
- **Secure Environment**: Locked-down interface during active examinations

### Anti-Cheat System

The proctoring system implements a multi-layered security approach to detect and prevent academic dishonesty:

#### **Browser-Level Monitoring**
During active test sessions, the application continuously monitors:
- **Tab Switching Detection**: Logs any attempts to navigate away from the test window
- **Copy/Paste Prevention**: Blocks and records clipboard operations
- **Fullscreen Enforcement**: Ensures the application remains in fullscreen mode, preventing access to external resources
- **Keyboard Shortcuts**: Restricts system-level shortcuts that could be used to circumvent security

#### **Camera-Based ML Monitoring**

When a student begins a test, the system spawns an independent camera monitoring process that employs custom-trained machine learning models to analyze the video feed in real-time.

**Optimized Camera Processing Pipeline:**

1. **Video Capture**: OpenCV captures frames from the student's webcam
2. **Face Detection**: MediaPipe processes each frame to identify faces in view
3. **Face Count Validation**:
   - **No Face Detected**: Logs alert for student absence
   - **Multiple Faces Detected**: Logs potential unauthorized assistance
   - **Single Face Detected**: Proceeds to verification
4. **Identity Verification**: Validates the detected face against the registered student profile
5. **Eye Tracking**: Monitors gaze direction and patterns to detect:
   - Looking away from the screen
   - Reading from external sources
   - Suspicious eye movement patterns
6. **Object Detection**: Identifies unauthorized devices, specifically:
   - Mobile phones
   - Tablets
   - Other electronic devices

All suspicious activities detected by the camera monitoring system are timestamped and logged to a local log file with detailed context about the violation.

### Backend Services (Django REST API)

The backend provides a robust API layer for:
- **Authentication & Authorization**: JWT-based secure user authentication
- **Test Management**: CRUD operations for assessments
- **Results Processing**: Score calculation and storage
- **Risk Score Evaluation**: Analyzes proctoring logs to generate comprehensive risk scores
- **Data Persistence**: MongoDB integration for scalable data storage

### Machine Learning Pipeline

The system leverages multiple specialized ML models:

- **Face Detection Model**: MediaPipe Face Detection for real-time face localization
- **Face Recognition Model**: DeepFace-based identity verification
- **Phone Detection Model**: Custom-trained YOLO model for mobile device detection
- **Eye Tracking Model**: MediaPipe Face Mesh for gaze estimation and eye movement analysis

### Data Flow

1. **Test Initiation**: Student logs in and starts a test
2. **Environment Lock**: Application enters fullscreen mode with monitoring active
3. **Dual Monitoring**:
   - Browser events logged in real-time
   - Camera feed processed by ML pipeline
4. **Local Logging**: All violations stored in structured log files
5. **Test Submission**: Upon completion, logs are transmitted to the backend
6. **Risk Analysis**: Backend evaluates logs and calculates a risk score
7. **Report Generation**: Administrators receive detailed proctoring reports

### Security Features

- **Encrypted Communication**: All client-server communication secured via HTTPS
- **JWT Authentication**: Stateless authentication for API requests
- **Local Log Encryption**: Proctoring logs encrypted before transmission
- **Tamper Detection**: Logs include checksums to prevent manipulation
- **Process Isolation**: Camera monitoring runs in isolated process

## Project Structure

```
├── frontend/
│   ├── ai-proctor/          # React web application
│   └── Proctor_App/         # Electron desktop application
├── backend/
│   ├── apps/                # Django applications (authentication, proctoring, tests, results)
│   ├── middleware/          # Custom middleware
│   └── utils/               # JWT auth, MongoDB client
├── HD_ML_stuff/             # Machine learning proctoring pipeline
│   ├── modules/             # Core ML modules
│   ├── cv_models/           # Pre-trained models
│   └── logs/                # Proctoring and eye movement logs
└── HD_Py_Bundler/           # Python to executable bundler

```

## Setup Instructions

### Prerequisites
- Node.js (v16+)
- Python (3.8+)
- MongoDB
- Webcam for proctoring features

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend/Proctor_App
npm install
npm run dev
```

### ML Pipeline Setup
```bash
cd HD_ML_stuff
pip install -r requirements.txt
# Download required models to cv_models/
python proctor_main.py
```

## Development Guidelines

- Make changes only in your respective folders
- Use appropriate `.gitignore` files to avoid committing large model files or dependencies
- Provide clear documentation in module-specific README files
- Follow code style conventions for each language/framework

## Technology Stack

**Frontend**: React, Electron, Vite, TailwindCSS  
**Backend**: Django, Django REST Framework, MongoDB  
**ML/CV**: OpenCV, MediaPipe, DeepFace, YOLO, NumPy  
**Authentication**: JWT (JSON Web Tokens)  
**Deployment**: Electron Builder

## License

This project is developed for academic purposes.

---

**Team**: RUBIX26_15_ICodeSpeed