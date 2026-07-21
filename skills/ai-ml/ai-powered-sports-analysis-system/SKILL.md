---
name: ai-powered-sports-analysis-system
description: Build AI-powered sports training analysis systems with adaptive learning capabilities. Includes pose estimation, video analysis, personalized feedback generation, and multi-platform deployment.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ai, ml, computer-vision, sports, pose-estimation, adaptive-learning, full-stack, flutter, fastapi]
    related_skills: [writing-plans, subagent-driven-development, test-driven-development]
---

# AI-Powered Sports Analysis System Development

## Overview

Build complete AI-powered sports training analysis systems with these key capabilities:
- **Video capture** from mobile devices
- **Pose estimation** using MediaPipe/OpenPose
- **Object detection** using YOLO
- **Adaptive learning** with GMM and clustering algorithms
- **Personalized feedback** generation
- **Multi-platform deployment** (Mobile + Web + Backend)

## When to Use

Use this skill when building:
- Sports training analysis apps (basketball, golf, tennis, etc.)
- Fitness form correction systems
- Movement analysis platforms
- Any application requiring pose estimation + personalized feedback

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
├─────────────────────────────────────────────────────────────┤
│  Mobile App (Flutter)  │  Web Frontend (React)            │
│  • Video recording       │  • Dashboard                    │
│  • Real-time preview     │  • Analytics                    │
│  • Results display       │  • Admin panel                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                   │
│              Auth / Rate Limit / Logging / Routing           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Microservices                           │
├─────────────────────────────────────────────────────────────┤
│  Video Processing  │  ML Service  │  User Service          │
│  • Upload/Storage  │  • Pose Est  │  • Auth/Profile        │
│  • Preprocessing   │  • Detection │  • Subscriptions       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Data Layer                            │
├─────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis  │  MinIO  │  Qdrant (Vector DB)   │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Pose Estimation Module

**Technology**: MediaPipe Pose

```python
# ml-service/app/models/pose_estimator.py
import mediapipe as mp
import numpy as np

class PoseEstimator:
    """Wrapper for MediaPipe pose estimation"""
    
    def __init__(self, model_complexity=2):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def estimate(self, image):
        """Extract 25 keypoints from image"""
        results = self.pose.process(image)
        if not results.pose_landmarks:
            return None
        
        # Extract keypoints
        landmarks = results.pose_landmarks.landmark
        keypoints = {
            'nose': self._get_landmark(landmarks, self.mp_pose.PoseLandmark.NOSE),
            'left_shoulder': self._get_landmark(...),
            'right_shoulder': self._get_landmark(...),
            # ... all 25 keypoints
        }
        
        # Calculate angles
        keypoints['elbow_angle'] = self._calculate_angle(...)
        keypoints['knee_angle'] = self._calculate_angle(...)
        
        return keypoints
```

### 2. Object Detection Module

**Technology**: YOLOv8

```python
# ml-service/app/models/shot_detector.py
from ultralytics import YOLO

class ShotDetector:
    """Wrapper for YOLO object detection"""
    
    def __init__(self, model_path=None):
        if model_path:
            self.model = YOLO(model_path)
        else:
            self.model = YOLO('yolov8n.pt')  # Use COCO pretrained
    
    def detect(self, image):
        """Detect objects in image"""
        results = self.model(image)
        detections = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                detection = {
                    'class': self.model.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist()
                }
                detections.append(detection)
        
        return detections
```

### 3. Adaptive Learning Engine

**Core Algorithm**: Gaussian Mixture Model (GMM) + HDBSCAN

```python
# ml-service/app/models/adaptive_engine.py
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from hdbscan import HDBSCAN
import numpy as np

class AdaptiveEngine:
    """
    Adaptive learning engine for personalized feedback
    
    Three-tier model:
    1. Base model: Pre-trained on public datasets
    2. Group model: GMM trained on all platform data
    3. Personal model: Fine-tuned on individual user data
    """
    
    def __init__(self, model_dir="/app/models"):
        self.feature_extractor = PoseFeatureExtractor()
        self.group_model = GroupPoseModel()
        self.error_recognizer = ErrorPatternRecognizer()
        self.personal_models = {}
    
    def assess(self, user_id, pose_sequence, user_history=None):
        """
        Complete assessment pipeline:
        1. Extract features from pose sequence
        2. Compare with appropriate model (personal > group > base)
        3. Identify error patterns using HDBSCAN clustering
        4. Generate personalized feedback
        """
        # 1. Feature extraction
        feature = self.feature_extractor.extract(pose_sequence)
        
        # 2. Select model (personal > group)
        model = self._get_user_model(user_id)
        
        # 3. Calculate similarity score
        score = model.score(feature)
        
        # 4. Calculate residual (difference from standard)
        residual = feature - model.mean_
        
        # 5. Identify error patterns
        errors = self.error_recognizer.recognize(residual)
        
        # 6. Generate feedback
        feedback = self._generate_feedback(score, errors, user_history)
        
        return feedback


class GroupPoseModel:
    """GMM-based group model"""
    
    def __init__(self, n_components=5):
        self.model = GaussianMixture(
            n_components=n_components,
            covariance_type='full',
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def fit(self, features):
        """Train on all platform data"""
        scaled = self.scaler.fit_transform(features)
        self.model.fit(scaled)
        self.is_fitted = True
    
    def score(self, feature):
        """Calculate similarity score (0-1)"""
        if not self.is_fitted:
            return 0.5
        
        scaled = self.scaler.transform(feature.reshape(1, -1))
        log_prob = self.model.score_samples(scaled)[0]
        
        # Convert to 0-1 score
        score = 1.0 / (1.0 + np.exp(-(log_prob + 50) / 10))
        return float(np.clip(score, 0.0, 1.0))


class ErrorPatternRecognizer:
    """HDBSCAN-based error pattern recognition"""
    
    ERROR_PATTERNS = {
        'elbow_flare': {
            'name': 'Elbow Flare',
            'suggestions': [
                'Strengthen wrist muscles',
                'Imagine elbow tucking inward',
                'Watch reference video'
            ]
        },
        'knee_dip': {
            'name': 'Knee Dip',
            'suggestions': [
                'Strengthen leg muscles',
                'Practice jumping motion',
                'Focus on upward push'
            ]
        }
    }
    
    def __init__(self):
        self.model = HDBSCAN(
            min_cluster_size=5,
            min_samples=3,
            metric='euclidean'
        )
        self.scaler = StandardScaler()
        self.cluster_to_pattern = {}
    
    def fit(self, residual_vectors, labels):
        """Train on labeled error samples"""
        scaled = self.scaler.fit_transform(residual_vectors)
        clusters = self.model.fit_predict(scaled)
        
        # Map clusters to error labels
        from collections import Counter
        for cluster_id in set(clusters):
            if cluster_id == -1:
                continue
            mask = clusters == cluster_id
            most_common = Counter(np.array(labels)[mask]).most_common(1)
            if most_common:
                self.cluster_to_pattern[cluster_id] = most_common[0][0]
    
    def recognize(self, residual_vector):
        """Identify error patterns in residual"""
        scaled = self.scaler.transform(residual_vector.reshape(1, -1))
        cluster = self.model.predict(scaled)[0]
        
        if cluster == -1:
            return []
        
        pattern_key = self.cluster_to_pattern.get(cluster)
        if not pattern_key:
            return []
        
        pattern_info = self.ERROR_PATTERNS.get(pattern_key, {})
        
        return [{
            'pattern': pattern_info.get('name', 'Unknown'),
            'severity': self._calculate_severity(cluster),
            'suggestions': pattern_info.get('suggestions', [])
        }]
```

## Development Workflow

### Phase 1: Foundation (Days 1-5)

```markdown
### Task 1.1: Database Models
**Priority**: P0 (Blocking)
**Time**: 4-6 hours

Create SQLAlchemy models:
- User (id, profile, subscription_type, wechat_openid)
- Training (id, user_id, video_url, status, metrics)
- Shot (id, training_id, pose_data, score)
- PoseModel (id, model_type, model_data)
- ErrorPattern (id, name, cluster_id, suggestions)

Files:
- backend/app/models/user.py
- backend/app/models/training.py
- backend/app/models/shot.py
- backend/app/models/pose_model.py
- backend/app/models/error_pattern.py

### Task 1.2: Pydantic Schemas
**Priority**: P0
**Time**: 2-3 hours

Create request/response schemas matching models.

### Task 1.3: Database Migration
**Priority**: P0
**Time**: 1-2 hours

Configure Alembic and generate initial migration.

Commands:
```bash
cd backend
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```
```

### Phase 2: Backend API (Days 6-10)

```markdown
### Task 2.1: Authentication
**Priority**: P0
**Time**: 3-4 hours

Implement WeChat OAuth login:
- POST /auth/wechat
- JWT token generation
- Token refresh

### Task 2.2: Training API
**Priority**: P0
**Time**: 4-6 hours

- POST /trainings (upload video)
- GET /trainings (list with pagination)
- GET /trainings/{id} (get details)
- GET /trainings/{id}/status (check analysis status)

### Task 2.3: Analysis API
**Priority**: P0
**Time**: 3-4 hours

- POST /analysis/feedback (quick image analysis)
- POST /analysis/compare (compare multiple trainings)
- GET /analysis/trends (progress over time)
```

### Phase 3: ML Service (Days 11-13)

```markdown
### Task 3.1: Pose Estimation
**Priority**: P0
**Time**: 3-4 hours

Integrate MediaPipe for 25-keypoint detection.

### Task 3.2: Object Detection
**Priority**: P0
**Time**: 3-4 hours

Integrate YOLOv8 for ball/person detection.

### Task 3.3: Adaptive Engine
**Priority**: P0
**Time**: 6-8 hours

Implement GMM group model and HDBSCAN error recognition.
```

### Phase 4: Flutter App (Days 14-20)

```markdown
### Task 4.1: Project Setup
**Priority**: P0
**Time**: 2-3 hours

Initialize Flutter project with:
- camera plugin
- http/dio for API
- state management (Bloc/Provider)

### Task 4.2: Video Recording
**Priority**: P0
**Time**: 6-8 hours

- Camera preview
- Recording controls
- Upload to backend

### Task 4.3: Results Display
**Priority**: P0
**Time**: 6-8 hours

- Score display with animation
- Video playback with keypoint overlay
- Feedback cards
- Share functionality
```

### Phase 5: Deployment (Days 21-25)

```markdown
### Task 5.1: Docker Configuration
**Priority**: P0
**Time**: 4-6 hours

Create docker-compose.yml with:
- nginx (reverse proxy)
- backend (FastAPI)
- ml-service (Python)
- postgres (database)
- redis (cache)
- minio (object storage)

### Task 5.2: Production Setup
**Priority**: P0
**Time**: 3-4 hours

- SSL certificates
- Environment variables
- Backup scripts
- Monitoring
```

## Key Technical Decisions

### 1. Feature Extraction

Extract these features from pose sequences:
- **Joint angles**: Elbow, knee, hip angles
- **Temporal features**: Mean, std, min, max of angles over time
- **Symmetry**: Left-right balance
- **Trajectory**: Ball path curvature

```python
def extract_features(pose_sequence):
    features = []
    
    # Joint angles
    for pose in pose_sequence:
        features.extend([
            pose['elbow_angle'],
            pose['knee_angle'],
            pose['hip_angle']
        ])
    
    # Temporal statistics
    angles = [p['elbow_angle'] for p in pose_sequence]
    features.extend([
        np.mean(angles),
        np.std(angles),
        np.min(angles),
        np.max(angles)
    ])
    
    return np.array(features)
```

### 2. Model Update Strategy

| Model | Update Frequency | Data Source |
|-------|-----------------|-------------|
| Group Model | Weekly | All platform users (anonymized) |
| Error Recognizer | Monthly | Labeled error samples |
| Personal Model | Real-time | Individual user history |

### 3. Scoring Algorithm

```python
score = (
    pose_similarity * 0.4 +      # Cosine similarity to standard
    trajectory_quality * 0.3 +   # Parabola smoothness
    success_rate * 0.2 +         # Made shots percentage
    consistency * 0.1           # Variance across attempts
) * 100
```

## Common Pitfalls

### 1. Pose Estimation Accuracy

**Problem**: MediaPipe may fail with occluded limbs or poor lighting.

**Solution**:
- Add confidence threshold filtering
- Implement fallback to previous frame
- Guide user with on-screen positioning hints

### 2. Model Cold Start

**Problem**: New users have no personal model; group model may not fit.

**Solution**:
- Use group model for first 5 attempts
- After 5 attempts, start personal model training
- Blend group and personal scores: `score = 0.7 * personal + 0.3 * group`

### 3. Real-time Feedback Delay

**Problem**: Video analysis takes 2-3x video duration.

**Solution**:
- Process asynchronously (Celery/Redis Queue)
- Show progress indicator
- Send push notification when complete
- Cache results for instant replay

## Testing Strategy

### Unit Tests

```python
# Test feature extraction
def test_feature_extraction():
    pose_sequence = generate_mock_poses()
    features = extract_features(pose_sequence)
    assert len(features) == EXPECTED_DIM
    assert not np.isnan(features).any()

# Test GMM scoring
def test_gmm_score_range():
    model = GroupPoseModel()
    model.fit(mock_features)
    score = model.score(test_feature)
    assert 0 <= score <= 1
```

### Integration Tests

```python
# Test full pipeline
def test_analysis_pipeline():
    video = upload_test_video()
    training_id = create_training(video)
    
    # Wait for processing
    wait_for_status(training_id, "completed", timeout=60)
    
    result = get_analysis_result(training_id)
    assert result['score'] > 0
    assert len(result['suggestions']) > 0
```

## Deployment Checklist

- [ ] Docker images build successfully
- [ ] Database migrations run without errors
- [ ] ML models load correctly
- [ ] API endpoints respond correctly
- [ ] Authentication works (WeChat OAuth)
- [ ] File uploads work (MinIO)
- [ ] Video processing completes
- [ ] Results display correctly
- [ ] Push notifications work
- [ ] SSL certificates configured
- [ ] Backup scripts tested
- [ ] Monitoring dashboards active

## Resources

- **MediaPipe Pose**: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- **YOLOv8**: https://docs.ultralytics.com/
- **HDBSCAN**: https://hdbscan.readthedocs.io/
- **GMM**: https://scikit-learn.org/stable/modules/mixture.html

## Remember

```
1. Start with data models — everything depends on them
2. Test ML components with synthetic data before real data
3. Adaptive learning requires user data — plan cold start strategy
4. Video processing is async — design for latency
5. Personalization is the differentiator — invest in adaptive engine
```
